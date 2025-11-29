
import json
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, desc, func, text, String
from sqlalchemy.orm import sessionmaker, Session
from phi.agent import Agent, AgentMemory
from phi.model.openai import OpenAIChat
from phi.storage.agent.postgres import PgAgentStorage
from phi.memory.db.postgres import PgMemoryDb
from phi.knowledge.text import TextKnowledgeBase
from phi.vectordb.pgvector import PgVector, SearchType
from phi.utils.log import logger
from phi.document import Document
import os
import hashlib
import uuid
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class MeetingChatbot:
    def __init__(self, mysql_db_url: str, vector_db_url: str, meeting_model):
        """
        Initialize the meeting chatbot with proper error handling and validation
        
        Args:
            mysql_db_url: MySQL database URL (e.g., "mysql+pymysql://user:password@host:port/database")
            vector_db_url: PostgreSQL URL for vector storage
            meeting_model: Your SQLAlchemy Meeting model class
        """
        try:
            self.mysql_engine = create_engine(
                mysql_db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.mysql_engine)
            self.vector_db_url = vector_db_url
            self.Meeting = meeting_model
            self.agents = {}
            self.knowledge_bases = {}
            
            # Track processed meetings per user to avoid reprocessing
            self.processed_meetings = {}  # user_id -> set of meeting content hashes
            
            # Test connections
            self._test_database_connections()
            logger.info("MeetingChatbot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MeetingChatbot: {e}")
            raise

    def _test_database_connections(self):
        """Test database connections"""
        try:
            # Test MySQL connection
            with self.SessionLocal() as db:
                db.execute(text("SELECT 1"))
            logger.info("MySQL connection successful")
            
            # Test PostgreSQL connection (vector DB)
            import psycopg2
            from urllib.parse import urlparse
            parsed = urlparse(self.vector_db_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:]  # Remove leading slash
            )
            conn.close()
            logger.info("PostgreSQL connection successful")
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise

    def create_meeting_tools(self, user_id: str):
        """Create user-specific database tools with enhanced error handling"""
        
        def get_user_meetings(
            limit: int = 10,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            platform: Optional[str] = None,
            status: Optional[str] = None,
            workspace_id: Optional[int] = None
        ) -> str:
            """Get meetings for the current user only with comprehensive filtering"""
            try:
                with self.SessionLocal() as db:
                    query = db.query(self.Meeting).filter(self.Meeting.user_id == user_id)
                    
                    # Add filters with proper error handling
                    if start_date:
                        try:
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            query = query.filter(self.Meeting.started_date_time_utc >= start_dt)
                        except ValueError as e:
                            logger.warning(f"Invalid start_date format: {start_date}, error: {e}")
                    
                    if end_date:
                        try:
                            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            query = query.filter(self.Meeting.ended_date_time_utc <= end_dt)
                        except ValueError as e:
                            logger.warning(f"Invalid end_date format: {end_date}, error: {e}")
                    
                    if platform:
                        query = query.filter(self.Meeting.platform.ilike(f"%{platform}%"))
                    
                    if status:
                        query = query.filter(self.Meeting.status == status)
                    
                    if workspace_id:
                        query = query.filter(self.Meeting.workspace_id == workspace_id)
                    
                    # Order by most recent and limit
                    meetings = query.order_by(desc(self.Meeting.started_date_time_utc)).limit(limit).all()
                    
                    # Convert to dict format with safe attribute access
                    results = []
                    for meeting in meetings:
                        try:
                            results.append({
                                'id': getattr(meeting, 'id', None),
                                'session_id': getattr(meeting, 'session_id', None),
                                'meeting_id': getattr(meeting, 'meeting_id', None),
                                'title': getattr(meeting, 'title', 'Untitled'),
                                'platform': getattr(meeting, 'platform', None),
                                'started_date_time_utc': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                                'ended_date_time_utc': meeting.ended_date_time_utc.isoformat() if getattr(meeting, 'ended_date_time_utc', None) else None,
                                'total_speakers_count': getattr(meeting, 'total_speakers_count', 0),
                                'speaker_list': getattr(meeting, 'speaker_list', []),
                                'status': meeting.status.value if meeting.status else 'unknown',
                                'is_completed': getattr(meeting, 'is_completed', False),
                                'workspace_id': getattr(meeting, 'workspace_id', None),
                                'summary': getattr(meeting, 'summary', None)
                            })
                        except Exception as e:
                            logger.error(f"Error processing meeting {getattr(meeting, 'id', 'unknown')}: {e}")
                            continue
                    
                    return json.dumps({
                        "meetings": results,
                        "count": len(results),
                        "total_available": query.count() if limit < 100 else "many"
                    }, indent=2)
                    
            except Exception as e:
                logger.error(f"Error fetching meetings for user {user_id}: {e}")
                return json.dumps({"error": f"Error fetching meetings: {str(e)}"})

        def get_meeting_details(meeting_session_id: str) -> str:
            """Get full meeting details including transcription with user verification"""
            try:
                with self.SessionLocal() as db:
                    meeting = db.query(self.Meeting).filter(
                        and_(
                            self.Meeting.session_id == meeting_session_id,
                            self.Meeting.user_id == user_id
                        )
                    ).first()
                    
                    if not meeting:
                        return json.dumps({"error": "Meeting not found or access denied"})
                    
                    # Safely extract all attributes
                    result = {
                        'id': getattr(meeting, 'id', None),
                        'session_id': getattr(meeting, 'session_id', None),
                        'meeting_id': getattr(meeting, 'meeting_id', None),
                        'title': getattr(meeting, 'title', 'Untitled'),
                        'platform': getattr(meeting, 'platform', None),
                        'meeting_url': getattr(meeting, 'meeting_url', None),
                        'started_date_time_utc': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                        'ended_date_time_utc': meeting.ended_date_time_utc.isoformat() if getattr(meeting, 'ended_date_time_utc', None) else None,
                        'total_speakers_count': getattr(meeting, 'total_speakers_count', 0),
                        'speaker_list': getattr(meeting, 'speaker_list', []),
                        'transcription_json': getattr(meeting, 'transcription_json', None),
                        'summary': getattr(meeting, 'summary', None),
                        'status': meeting.status.value if meeting.status else 'unknown',
                        'is_completed': getattr(meeting, 'is_completed', False),
                        'workspace_id': getattr(meeting, 'workspace_id', None),
                        'recording_path': getattr(meeting, 'recording_path', None)
                    }
                    
                    return json.dumps(result, indent=2)
                        
            except Exception as e:
                logger.error(f"Error fetching meeting details: {e}")
                return json.dumps({"error": f"Failed to fetch meeting details: {str(e)}"})

        def search_meetings_by_keyword(
            keyword: str,
            limit: int = 5,
            search_in_transcription: bool = True,
            search_in_summary: bool = True,
            search_in_title: bool = True
        ) -> str:
            """Search meetings by keyword with improved search logic"""
            try:
                with self.SessionLocal() as db:
                    query = db.query(self.Meeting).filter(self.Meeting.user_id == user_id)
                    
                    # Build search conditions
                    search_conditions = []
                    keyword_pattern = f"%{keyword}%"
                    
                    if search_in_title and hasattr(self.Meeting, 'title'):
                        search_conditions.append(self.Meeting.title.ilike(keyword_pattern))
                    
                    if search_in_transcription and hasattr(self.Meeting, 'transcription_json'):
                        # Handle both string and JSON fields
                        search_conditions.append(
                            func.cast(self.Meeting.transcription_json, String).ilike(keyword_pattern)
                        )
                    
                    if search_in_summary and hasattr(self.Meeting, 'summary'):
                        search_conditions.append(
                            func.cast(self.Meeting.summary, String).ilike(keyword_pattern)
                        )
                    
                    if search_conditions:
                        query = query.filter(or_(*search_conditions))
                    
                    meetings = query.order_by(desc(self.Meeting.started_date_time_utc)).limit(limit).all()
                    
                    results = []
                    for meeting in meetings:
                        results.append({
                            'id': getattr(meeting, 'id', None),
                            'session_id': getattr(meeting, 'session_id', None),
                            'title': getattr(meeting, 'title', 'Untitled'),
                            'platform': getattr(meeting, 'platform', None),
                            'started_date_time_utc': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                            'ended_date_time_utc': meeting.ended_date_time_utc.isoformat() if getattr(meeting, 'ended_date_time_utc', None) else None,
                            'total_speakers_count': getattr(meeting, 'total_speakers_count', 0),
                            'speaker_list': getattr(meeting, 'speaker_list', []),
                            'summary': getattr(meeting, 'summary', None),
                            'status': meeting.status.value if meeting.status else 'unknown',
                            'workspace_id': getattr(meeting, 'workspace_id', None)
                        })
                    
                    return json.dumps({
                        "keyword": keyword,
                        "meetings": results,
                        "count": len(results)
                    }, indent=2)
                    
            except Exception as e:
                logger.error(f"Error searching meetings: {e}")
                return json.dumps({"error": f"Search failed: {str(e)}"})

        def get_meeting_analytics(days: int = 30) -> str:
            """Get comprehensive meeting analytics for the user"""
            try:
                with self.SessionLocal() as db:
                    # Calculate date range
                    start_date = datetime.utcnow() - timedelta(days=days)
                    
                    # Base query for the time period
                    base_query = db.query(self.Meeting).filter(
                        and_(
                            self.Meeting.user_id == user_id,
                            self.Meeting.started_date_time_utc >= start_date
                        )
                    )
                    
                    # Total meetings
                    total_meetings = base_query.count()
                    
                    # Completed meetings
                    completed_meetings = base_query.filter(self.Meeting.is_completed == True).count()
                    
                    # Platform breakdown with error handling
                    try:
                        platform_stats = db.query(
                            self.Meeting.platform,
                            func.count(self.Meeting.id).label('count')
                        ).filter(
                            and_(
                                self.Meeting.user_id == user_id,
                                self.Meeting.started_date_time_utc >= start_date
                            )
                        ).group_by(self.Meeting.platform).all()
                        platform_breakdown = {platform or 'Unknown': count for platform, count in platform_stats}
                    except Exception as e:
                        logger.warning(f"Error getting platform stats: {e}")
                        platform_breakdown = {}
                    
                    # Duration calculations with better error handling
                    meetings_with_duration = base_query.filter(
                        and_(
                            self.Meeting.started_date_time_utc.isnot(None),
                            self.Meeting.ended_date_time_utc.isnot(None)
                        )
                    ).all()
                    
                    total_duration_minutes = 0
                    duration_count = 0
                    
                    for meeting in meetings_with_duration:
                        try:
                            if meeting.started_date_time_utc and meeting.ended_date_time_utc:
                                duration = meeting.ended_date_time_utc - meeting.started_date_time_utc
                                if duration.total_seconds() > 0:  # Ensure positive duration
                                    total_duration_minutes += duration.total_seconds() / 60
                                    duration_count += 1
                        except Exception as e:
                            logger.warning(f"Error calculating duration for meeting {meeting.id}: {e}")
                            continue
                    
                    avg_duration_minutes = total_duration_minutes / duration_count if duration_count > 0 else 0
                    
                    # Latest meeting
                    latest_meeting = base_query.order_by(desc(self.Meeting.started_date_time_utc)).first()
                    
                    # Speaker analytics
                    total_speakers = 0
                    meetings_with_speakers = 0
                    for meeting in base_query.all():
                        speaker_count = getattr(meeting, 'total_speakers_count', 0) or 0
                        if speaker_count > 0:
                            total_speakers += speaker_count
                            meetings_with_speakers += 1
                    
                    avg_speakers = total_speakers / meetings_with_speakers if meetings_with_speakers > 0 else 0
                    
                    analytics = {
                        'period_days': days,
                        'total_meetings': total_meetings,
                        'completed_meetings': completed_meetings,
                        'completion_rate': (completed_meetings / total_meetings * 100) if total_meetings > 0 else 0,
                        'avg_duration_minutes': round(avg_duration_minutes, 2),
                        'total_duration_minutes': round(total_duration_minutes, 2),
                        'total_duration_hours': round(total_duration_minutes / 60, 2),
                        'platform_breakdown': platform_breakdown,
                        'avg_speakers_per_meeting': round(avg_speakers, 2),
                        'latest_meeting_date': latest_meeting.started_date_time_utc.isoformat() if latest_meeting and getattr(latest_meeting, 'started_date_time_utc', None) else None,
                        'meetings_with_valid_duration': duration_count
                    }
                    
                    return json.dumps(analytics, indent=2)
                    
            except Exception as e:
                logger.error(f"Error getting analytics: {e}")
                return json.dumps({"error": f"Failed to fetch analytics: {str(e)}"})

        def get_meetings_by_platform(platform: str, limit: int = 10) -> str:
            """Get meetings filtered by platform"""
            try:
                with self.SessionLocal() as db:
                    meetings = db.query(self.Meeting).filter(
                        and_(
                            self.Meeting.user_id == user_id,
                            self.Meeting.platform.ilike(f"%{platform}%")
                        )
                    ).order_by(desc(self.Meeting.started_date_time_utc)).limit(limit).all()
                    
                    results = []
                    for meeting in meetings:
                        results.append({
                            'id': getattr(meeting, 'id', None),
                            'session_id': getattr(meeting, 'session_id', None),
                            'title': getattr(meeting, 'title', 'Untitled'),
                            'platform': getattr(meeting, 'platform', None),
                            'started_date_time_utc': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                            'ended_date_time_utc': meeting.ended_date_time_utc.isoformat() if getattr(meeting, 'ended_date_time_utc', None) else None,
                            'total_speakers_count': getattr(meeting, 'total_speakers_count', 0),
                            'speaker_list': getattr(meeting, 'speaker_list', []),
                            'status': meeting.status.value if meeting.status else 'unknown',
                            'is_completed': getattr(meeting, 'is_completed', False),
                            'workspace_id': getattr(meeting, 'workspace_id', None)
                        })
                    
                    return json.dumps({
                        "platform": platform,
                        "meetings": results,
                        "count": len(results)
                    }, indent=2)
                    
            except Exception as e:
                logger.error(f"Error fetching meetings by platform: {e}")
                return json.dumps({"error": f"Failed to fetch platform meetings: {str(e)}"})

        def get_workspace_meetings(workspace_id: int, limit: int = 10) -> str:
            """Get meetings for a specific workspace"""
            try:
                with self.SessionLocal() as db:
                    meetings = db.query(self.Meeting).filter(
                        and_(
                            self.Meeting.user_id == user_id,
                            self.Meeting.workspace_id == workspace_id
                        )
                    ).order_by(desc(self.Meeting.started_date_time_utc)).limit(limit).all()
                    
                    results = []
                    for meeting in meetings:
                        results.append({
                            'id': getattr(meeting, 'id', None),
                            'session_id': getattr(meeting, 'session_id', None),
                            'title': getattr(meeting, 'title', 'Untitled'),
                            'platform': getattr(meeting, 'platform', None),
                            'started_date_time_utc': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                            'ended_date_time_utc': meeting.ended_date_time_utc.isoformat() if getattr(meeting, 'ended_date_time_utc', None) else None,
                            'total_speakers_count': getattr(meeting, 'total_speakers_count', 0),
                            'speaker_list': getattr(meeting, 'speaker_list', []),
                            'status': meeting.status.value if meeting.status else 'unknown',
                            'is_completed': getattr(meeting, 'is_completed', False),
                            'workspace_id': getattr(meeting, 'workspace_id', None)
                        })
                    
                    return json.dumps({
                        "workspace_id": workspace_id,
                        "meetings": results,
                        "count": len(results)
                    }, indent=2)
                    
            except Exception as e:
                logger.error(f"Error fetching workspace meetings: {e}")
                return json.dumps({"error": f"Failed to fetch workspace meetings: {str(e)}"})

        return [
            get_user_meetings,
            get_meeting_details,
            search_meetings_by_keyword,
            get_meeting_analytics,
            get_meetings_by_platform,
            get_workspace_meetings
        ]

    def _generate_document_id(self, meeting_id: int, doc_type: str, user_id: str) -> str:
        """Generate unique document ID with user isolation"""
        return f"user_{user_id}_meeting_{meeting_id}_{doc_type}_{uuid.uuid4().hex[:8]}"

    def _generate_content_hash(self, content: str) -> str:
        """Generate hash of content to detect duplicates"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _get_processed_meetings(self, user_id: str) -> Set[str]:
        """Get set of already processed meeting content hashes for a user"""
        if user_id not in self.processed_meetings:
            self.processed_meetings[user_id] = set()
        return self.processed_meetings[user_id]

    def _mark_meeting_processed(self, user_id: str, content_hash: str):
        """Mark a meeting as processed"""
        if user_id not in self.processed_meetings:
            self.processed_meetings[user_id] = set()
        self.processed_meetings[user_id].add(content_hash)

    def create_user_knowledge_base(self, user_id: str, force_refresh: bool = False) -> TextKnowledgeBase:
        """Create user-specific knowledge base with incremental updates"""
        
        # Check if we already have a knowledge base for this user and not forcing refresh
        if user_id in self.knowledge_bases and not force_refresh:
            logger.info(f"Returning existing knowledge base for user {user_id}")
            # Still check for new meetings to add incrementally
            self._update_knowledge_base_incrementally(user_id)
            return self.knowledge_bases[user_id]
        
        try:
            # Create knowledge base first
            knowledge_base = TextKnowledgeBase(
                path=f"user_{user_id}_meetings_knowledge",
                vector_db=PgVector(
                    table_name="user_meeting_knowledge",
                    db_url=self.vector_db_url,
                    search_type=SearchType.hybrid,
                    #collection=f"user_{user_id}_meetings"  # User-specific collection
                )
            )
            
            with self.SessionLocal() as db:
                # Get user's completed meetings with better filtering
                meetings_query = db.query(self.Meeting).filter(
                    and_(
                        self.Meeting.user_id == user_id,
                        self.Meeting.is_completed == True
                    )
                )
                
                # Add additional filters to ensure we have meaningful content
                meetings = meetings_query.filter(
                    or_(
                        self.Meeting.transcription_json.isnot(None),
                        self.Meeting.summary.isnot(None)
                    )
                ).order_by(desc(self.Meeting.started_date_time_utc)).all()
                
                logger.info(f"Found {len(meetings)} meetings with content for user {user_id}")
                
                if not meetings:
                    logger.warning(f"No meetings with content found for user {user_id}")
                    self.knowledge_bases[user_id] = knowledge_base
                    return knowledge_base
                
                # Get already processed meetings for this user
                processed_hashes = self._get_processed_meetings(user_id)
                
                # Prepare documents for knowledge base (only new ones)
                documents = []
                processed_count = 0
                new_documents_count = 0
                
                for meeting in meetings:
                    try:
                        # Process transcription
                        if hasattr(meeting, 'transcription_json') and meeting.transcription_json:
                            transcription_text = self._extract_text_from_transcription(
                                meeting.transcription_json
                            )
                            
                            if transcription_text and transcription_text.strip():
                                content_hash = self._generate_content_hash(f"transcription_{meeting.id}_{transcription_text}")
                                
                                if content_hash not in processed_hashes:
                                    doc_id = self._generate_document_id(meeting.id, 'transcription', user_id)
                                    
                                    documents.append(
                                        Document(
                                            id=doc_id,
                                            content=transcription_text,
                                            metadata={
                                                'meeting_id': meeting.id,
                                                'session_id': getattr(meeting, 'session_id', None),
                                                'external_meeting_id': getattr(meeting, 'meeting_id', None),
                                                'type': 'transcription',
                                                'title': getattr(meeting, 'title', 'Untitled Meeting'),
                                                'platform': getattr(meeting, 'platform', 'unknown'),
                                                'date': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                                                'user_id': user_id,
                                                'workspace_id': getattr(meeting, 'workspace_id', None),
                                                'speakers': getattr(meeting, 'speaker_list', []) or [],
                                                'speakers_count': getattr(meeting, 'total_speakers_count', 0) or 0,
                                                'content_hash': content_hash,
                                                'doc_type': 'transcription'
                                            }
                                        )
                                    )
                                    self._mark_meeting_processed(user_id, content_hash)
                                    new_documents_count += 1
                                else:
                                    processed_count += 1
                        
                        # Process summary
                        if hasattr(meeting, 'summary') and meeting.summary:
                            summary_text = self._extract_text_from_summary(meeting.summary)
                            
                            if summary_text and summary_text.strip():
                                content_hash = self._generate_content_hash(f"summary_{meeting.id}_{summary_text}")
                                
                                if content_hash not in processed_hashes:
                                    doc_id = self._generate_document_id(meeting.id, 'summary', user_id)
                                    
                                    documents.append(
                                        Document(
                                            id=doc_id,
                                            content=summary_text,
                                            metadata={
                                                'meeting_id': meeting.id,
                                                'session_id': getattr(meeting, 'session_id', None),
                                                'external_meeting_id': getattr(meeting, 'meeting_id', None),
                                                'type': 'summary',
                                                'title': getattr(meeting, 'title', 'Untitled Meeting'),
                                                'platform': getattr(meeting, 'platform', 'unknown'),
                                                'date': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                                                'user_id': user_id,
                                                'workspace_id': getattr(meeting, 'workspace_id', None),
                                                'speakers': getattr(meeting, 'speaker_list', []) or [],
                                                'speakers_count': getattr(meeting, 'total_speakers_count', 0) or 0,
                                                'content_hash': content_hash,
                                                'doc_type': 'summary'
                                            }
                                        )
                                    )
                                    self._mark_meeting_processed(user_id, content_hash)
                                    new_documents_count += 1
                                else:
                                    processed_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing meeting {meeting.id} for user {user_id}: {e}")
                        continue
                
                logger.info(f"Prepared {len(documents)} new documents for user {user_id} (skipped {processed_count} already processed)")
                
                # Load documents into knowledge base in smaller batches (only new ones)
                if documents:
                    batch_size = 5
                    successful_loads = 0
                    
                    for i in range(0, len(documents), batch_size):
                        batch = documents[i:i + batch_size]
                        try:
                            logger.info(f"Loading batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} with {len(batch)} documents")
                            knowledge_base.load_documents(batch, upsert=True)
                            successful_loads += len(batch)
                            logger.info(f"Successfully loaded batch {i//batch_size + 1}")
                        except Exception as e:
                            logger.error(f"Error loading batch {i//batch_size + 1}: {e}")
                            # Try loading documents one by one for this batch
                            for doc in batch:
                                try:
                                    knowledge_base.load_documents([doc], upsert=True)
                                    successful_loads += 1
                                    logger.info(f"Successfully loaded individual document {doc.id}")
                                except Exception as single_doc_error:
                                    logger.error(f"Error loading single document {doc.id}: {single_doc_error}")
                    
                    logger.info(f"Successfully loaded {successful_loads}/{len(documents)} new documents for user {user_id}")
                else:
                    logger.info(f"No new documents to load for user {user_id}")
                
                # Cache the knowledge base
                self.knowledge_bases[user_id] = knowledge_base
                
                logger.info(f"Successfully created knowledge base for user {user_id}")
                return knowledge_base
                
        except Exception as e:
            logger.error(f"Error creating knowledge base for user {user_id}: {e}")
            # Return basic knowledge base in case of error
            basic_kb = TextKnowledgeBase(
                path=f"user_{user_id}_meetings_basic",
                vector_db=PgVector(
                    table_name="user_meeting_knowledge",
                    db_url=self.vector_db_url,
                    search_type=SearchType.hybrid,
                    #collection=f"user_{user_id}_basic"
                )
            )
            self.knowledge_bases[user_id] = basic_kb
            return basic_kb

    def _update_knowledge_base_incrementally(self, user_id: str):
        """Update existing knowledge base with new meetings only"""
        try:
            if user_id not in self.knowledge_bases:
                logger.warning(f"No existing knowledge base found for user {user_id}")
                return
            
            knowledge_base = self.knowledge_bases[user_id]
            processed_hashes = self._get_processed_meetings(user_id)
            
            with self.SessionLocal() as db:
                # Get recent completed meetings that might be new
                recent_meetings = db.query(self.Meeting).filter(
                    and_(
                        self.Meeting.user_id == user_id,
                        self.Meeting.is_completed == True,
                        # Only check meetings from last 7 days to avoid processing everything
                        self.Meeting.started_date_time_utc >= datetime.utcnow() - timedelta(days=7)
                    )
                ).filter(
                    or_(
                        self.Meeting.transcription_json.isnot(None),
                        self.Meeting.summary.isnot(None)
                    )
                ).all()
                
                new_documents = []
                new_count = 0
                
                for meeting in recent_meetings:
                    try:
                        # Check transcription
                        if hasattr(meeting, 'transcription_json') and meeting.transcription_json:
                            transcription_text = self._extract_text_from_transcription(meeting.transcription_json)
                            if transcription_text and transcription_text.strip():
                                content_hash = self._generate_content_hash(f"transcription_{meeting.id}_{transcription_text}")
                                
                                if content_hash not in processed_hashes:
                                    doc_id = self._generate_document_id(meeting.id, 'transcription', user_id)
                                    new_documents.append(
                                        Document(
                                            id=doc_id,
                                            content=transcription_text,
                                            metadata={
                                                'meeting_id': meeting.id,
                                                'session_id': getattr(meeting, 'session_id', None),
                                                'external_meeting_id': getattr(meeting, 'meeting_id', None),
                                                'type': 'transcription',
                                                'title': getattr(meeting, 'title', 'Untitled Meeting'),
                                                'platform': getattr(meeting, 'platform', 'unknown'),
                                                'date': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                                                'user_id': user_id,
                                                'workspace_id': getattr(meeting, 'workspace_id', None),
                                                'speakers': getattr(meeting, 'speaker_list', []) or [],
                                                'speakers_count': getattr(meeting, 'total_speakers_count', 0) or 0,
                                                'content_hash': content_hash,
                                                'doc_type': 'transcription'
                                            }
                                        )
                                    )
                                    self._mark_meeting_processed(user_id, content_hash)
                                    new_count += 1
                        
                        # Check summary
                        if hasattr(meeting, 'summary') and meeting.summary:
                            summary_text = self._extract_text_from_summary(meeting.summary)
                            if summary_text and summary_text.strip():
                                content_hash = self._generate_content_hash(f"summary_{meeting.id}_{summary_text}")
                                
                                if content_hash not in processed_hashes:
                                    doc_id = self._generate_document_id(meeting.id, 'summary', user_id)
                                    new_documents.append(
                                        Document(
                                            id=doc_id,
                                            content=summary_text,
                                            metadata={
                                                'meeting_id': meeting.id,
                                                'session_id': getattr(meeting, 'session_id', None),
                                                'external_meeting_id': getattr(meeting, 'meeting_id', None),
                                                'type': 'summary',
                                                'title': getattr(meeting, 'title', 'Untitled Meeting'),
                                                'platform': getattr(meeting, 'platform', 'unknown'),
                                                'date': meeting.started_date_time_utc.isoformat() if getattr(meeting, 'started_date_time_utc', None) else None,
                                                'user_id': user_id,
                                                'workspace_id': getattr(meeting, 'workspace_id', None),
                                                'speakers': getattr(meeting, 'speaker_list', []) or [],
                                                'speakers_count': getattr(meeting, 'total_speakers_count', 0) or 0,
                                                'content_hash': content_hash,
                                                'doc_type': 'summary'
                                            }
                                        )
                                    )
                                    self._mark_meeting_processed(user_id, content_hash)
                                    new_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing meeting {meeting.id} for incremental update: {e}")
                        continue
                
                # Load new documents if any
                if new_documents:
                    try:
                        knowledge_base.load_documents(new_documents, upsert=True)
                        logger.info(f"Added {len(new_documents)} new documents to knowledge base for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error adding new documents to knowledge base: {e}")
                else:
                    logger.debug(f"No new documents to add for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error updating knowledge base incrementally for user {user_id}: {e}")

    def _extract_text_from_transcription(self, transcription: Any) -> str:
        """Enhanced text extraction from transcription with better error handling"""
        if not transcription:
            return ""
        
        try:
            text_parts = []
            
            # Handle string input (JSON string)
            if isinstance(transcription, str):
                try:
                    transcription = json.loads(transcription)
                except json.JSONDecodeError:
                    # If it's not JSON, treat as plain text
                    return transcription.strip()
            
            # Handle list of segments
            if isinstance(transcription, list):
                for segment in transcription:
                    if isinstance(segment, dict):
                        # Extract text with speaker and timestamp
                        text = segment.get('text', segment.get('content', segment.get('transcript', '')))
                        
                        if text and text.strip():
                            speaker = segment.get('speaker', segment.get('name', segment.get('speaker_name', 'Speaker')))
                            timestamp = segment.get('timestamp', segment.get('start_time', segment.get('start', '')))
                            
                            if timestamp:
                                text_parts.append(f"[{timestamp}] {speaker}: {text}")
                            else:
                                text_parts.append(f"{speaker}: {text}")
                    elif isinstance(segment, str):
                        text_parts.append(segment)
                    
            # Handle dictionary input
            elif isinstance(transcription, dict):
                # Check for segments key
                if 'segments' in transcription:
                    return self._extract_text_from_transcription(transcription['segments'])
                elif 'transcript' in transcription:
                    return self._extract_text_from_transcription(transcription['transcript'])
                elif 'text' in transcription:
                    return str(transcription['text'])
                elif 'content' in transcription:
                    return str(transcription['content'])
                else:
                    # Flatten dict to text
                    for key, value in transcription.items():
                        if isinstance(value, (str, int, float)) and str(value).strip():
                            text_parts.append(f"{key}: {value}")
                        elif isinstance(value, (list, dict)):
                            nested_text = self._extract_text_from_transcription(value)
                            if nested_text:
                                text_parts.append(f"{key}: {nested_text}")
            else:
                text_parts.append(str(transcription))
            
            result = '\n'.join(filter(None, text_parts))
            return result.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from transcription: {e}")
            return str(transcription) if transcription else ""

    def _extract_text_from_summary(self, summary: Any) -> str:
        """Enhanced text extraction from summary with better error handling"""
        if not summary:
            return ""
        
        try:
            text_parts = []
            
            # Handle string input (JSON string)
            if isinstance(summary, str):
                try:
                    summary = json.loads(summary)
                except json.JSONDecodeError:
                    # If it's not JSON, treat as plain text
                    return summary.strip()
            
            # Handle dictionary input
            if isinstance(summary, dict):
                for key, value in summary.items():
                    if isinstance(value, str) and value.strip():
                        text_parts.append(f"{key.replace('_', ' ').title()}: {value}")
                    elif isinstance(value, list) and value:
                        if all(isinstance(item, str) for item in value):
                            text_parts.append(f"{key.replace('_', ' ').title()}: {', '.join(filter(None, value))}")
                        else:
                            # Handle list of objects
                            for item in value:
                                if isinstance(item, dict):
                                    nested_text = self._extract_text_from_summary(item)
                                    if nested_text:
                                        text_parts.append(f"{key.replace('_', ' ').title()}: {nested_text}")
                                else:
                                    text_parts.append(f"{key.replace('_', ' ').title()}: {str(item)}")
                    elif isinstance(value, dict):
                        nested_text = self._extract_text_from_summary(value)
                        if nested_text:
                            text_parts.append(f"{key.replace('_', ' ').title()}: {nested_text}")
                    elif value is not None:
                        text_parts.append(f"{key.replace('_', ' ').title()}: {str(value)}")
                        
            # Handle list input
            elif isinstance(summary, list):
                for item in summary:
                    if isinstance(item, str) and item.strip():
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        nested_text = self._extract_text_from_summary(item)
                        if nested_text:
                            text_parts.append(nested_text)
                    else:
                        text_parts.append(str(item))
            else:
                text_parts.append(str(summary))
            
            result = '\n'.join(filter(None, text_parts))
            return result.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from summary: {e}")
            return str(summary) if summary else ""

    def get_or_create_agent(self, user_id: str) -> Agent:
        """Get or create user-specific agent with enhanced configuration and fixed memory"""
        
        if user_id not in self.agents:
            try:
                logger.info(f"Creating new agent for user {user_id}")
                
                # Create user-specific tools
                tools = self.create_meeting_tools(user_id)
                
                # Create user-specific knowledge base
                knowledge_base = self.create_user_knowledge_base(user_id)
                
                # Create enhanced memory configuration with proper settings
                memory_db = PgMemoryDb(
                    table_name="agent_memory",
                    db_url=self.vector_db_url,
                    schema="ai"
                )
                
                # Create agent storage with proper settings
                agent_storage = PgAgentStorage(
                    table_name="agent_sessions", 
                    db_url=self.vector_db_url,
                    schema="ai"
                )
                
                # Create agent with comprehensive configuration
                agent = Agent(
                    model=OpenAIChat(
                        id="gpt-4o-mini",
                        api_key=OPENAI_API_KEY
                    ),
                    
                    # User-specific storage and memory - KEY FIX HERE
                    storage=agent_storage,
                    user_id=user_id,  # This is crucial for memory to work
                    
                    # Enhanced memory configuration - KEY FIXES HERE
                    memory=AgentMemory(
                        db=memory_db,
                        create_user_memories=True,
                        create_session_summary=True,
                        update_user_memories_after_run=True,
                        update_session_summary_after_run=True
                    ),
                    
                    # Memory and history settings - KEY FIXES HERE
                    add_history_to_messages=True,
                    num_history_responses=5,  # Start with fewer to debug
                    create_memories=True,
                    update_memories=True,  # Enable memory updates
                    read_chat_history=True,  # Enable reading chat history
                    
                    # Knowledge base configuration
                    knowledge=knowledge_base,
                    search_knowledge=True,
                    
                    # Tools for database access
                    tools=tools,
                    show_tool_calls=False,
                    
                    # Agent identification
                    name=f"MeetingAssistant_{user_id}",
                    
                    # Enhanced system prompt
                    instructions=f"""
                    You are an intelligent meeting assistant for user {user_id}. You have access to their meeting data, transcriptions, and summaries.

                    SECURITY & ACCESS CONTROL:
                    - You can ONLY access data for user {user_id}
                    - Never share information about other users
                    - All database queries are automatically filtered for this user
                    - If asked about other users, politely decline and redirect to their own data

                    CAPABILITIES:
                    1. **Meeting Data Access**: Search, filter, and analyze meetings by date, platform, workspace, or keywords
                    2. **Content Search**: Find specific information across all meeting transcriptions and summaries
                    3. **Analytics**: Provide insights about meeting patterns, duration, frequency, and productivity
                    4. **Memory**: Remember previous conversations and user preferences
                    5. **Smart Responses**: Use both stored knowledge and real-time database queries

                    MEETING DATA STRUCTURE:
                    - Each meeting has: session_id, meeting_id, title, platform, dates, speakers, transcription, summary
                    - Platforms: Google Meet, Zoom, Teams, etc.
                    - Status: processing, completed, failed
                    - Only completed meetings have full transcriptions
                    - Meetings belong to workspaces and have speaker information

                    RESPONSE GUIDELINES:
                    - Be conversational and helpful
                    - Provide specific, actionable information
                    - Use meeting data to give context-aware responses
                    - When searching, explain what you found and suggest follow-up actions
                    - If no relevant data is found, suggest alternative searches or actions
                    - Remember user preferences and context from previous conversations

                    MEMORY BEHAVIOR:
                    - Remember important details from our conversations
                    - Build on previous discussions
                    - Reference past queries when relevant
                    - Learn user preferences over time

                    EXAMPLE INTERACTIONS:
                    - "Show me my meetings from last week"
                    - "Find meetings where we discussed project deadlines"
                    - "What were the key action items from my Zoom calls this month?"
                    - "Give me analytics on my meeting patterns"
                    - "Summarize the main points from yesterday's standup"

                    Always be proactive in helping users discover insights from their meeting data.
                    """,
                    
                    # Additional configurations for better performance
                    markdown=True,
                    debug_mode=False,  # Set to True only for debugging
                    add_datetime_to_instructions=True,
                    prevent_prompt_injection=True,
                    limit_tool_access=False,
                    
                    # Reasoning capabilities
                    reasoning=False,  # Disable to reduce complexity initially
                )
                
                # Initialize the agent properly by creating necessary tables
                try:
                    # This will create the required database tables if they don't exist
                    agent.create_memories = True
                    agent.update_memories = True
                    logger.info(f"Agent tables initialized for user {user_id}")
                except Exception as table_error:
                    logger.warning(f"Error initializing agent tables: {table_error}")
                
                self.agents[user_id] = agent
                logger.info(f"Successfully created agent for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error creating agent for user {user_id}: {e}")
                raise
        
        return self.agents[user_id]

    def chat(self, user_id: str, message: str, session_id: Optional[str] = None, meeting_session_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle user chat message with enhanced error handling and response formatting"""
        
        try:
            # Validate input
            if not user_id or not message:
                return {
                    "response": "Please provide a valid user ID and message.",
                    "success": False,
                    "error": "Invalid input parameters"
                }
            
            logger.info(f"Processing chat for user {user_id}, session: {session_id}")
            
            if meeting_session_id:
                # 1. Get the tool to fetch a single meeting's details
                details_tool = self.create_meeting_tools(user_id=user_id)[1]  # get_meeting_details tool is at index 1
                
                # 2. Retrieve the specific meeting's data
                meeting_data_str = details_tool(meeting_session_id=meeting_session_id)
            
                if not meeting_data_str:
                    return {
                        "response": f"I couldn't find the meeting with ID '{meeting_session_id}'. Please check the ID and try again.",
                        "success": False,
                        "error": "Meeting not found"
                    }

                try:
                    meeting_data = json.loads(meeting_data_str)
                    transcription_text = self._extract_text_from_transcription(meeting_data.get('transcription_json', ''))
                    summary_text = self._extract_text_from_summary(meeting_data.get('summary', ''))
                except json.JSONDecodeError:
                    return {
                        "response": f"I encountered an error processing the data for meeting '{meeting_session_id}'.",
                        "success": False,
                        "error": "JSON decode error"
                    }

                # 3. Augment the user message with the specific meeting content.
                # This is a form of Retrieval-Augmented Generation (RAG) within the prompt itself.
                augmented_message = f"""
                You are a meeting assistant. A user has a question about a specific meeting.
                
                Here is the user's question: {message}
                
                Here are the details for the meeting with session ID: {meeting_session_id}
                
                Meeting Title: {meeting_data.get('title', 'Untitled')}
                Summary: {summary_text}
                
                Full Transcription:
                {transcription_text}
                
                Please answer the user's question based ONLY on the information provided above. If the information is not present in the meeting details, state that you cannot find the answer within this specific meeting.
                """
                
                # 4. Use the main agent to run with the augmented message
                agent = self.get_or_create_agent(user_id)
                if session_id:
                    agent.session_id = session_id
                
                logger.info(f"Using augmented message for single meeting {meeting_session_id}")
                response = agent.run(augmented_message)

            else:
                # --- ORIGINAL FUNCTIONALITY ---
                # This is the original logic. Get or create the full agent
                agent = self.get_or_create_agent(user_id)
                # Set session ID if provided, otherwise use existing or generate new
                if session_id:
                    agent.session_id = session_id
                elif not hasattr(agent, 'session_id') or not agent.session_id:
                    agent.session_id = f"session_{user_id}_{uuid.uuid4().hex[:8]}"
                
                logger.info(f"Using session ID: {agent.session_id}")
            
                # Process the original message with the full knowledge base
                response = agent.run(message)
        
            # --- COMMON RESPONSE HANDLING ---
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            logger.info(f"Generated response for user {user_id}")
            
            # Return structured response
            return {
                "response": response_content,
                "success": True,
                "session_id": agent.session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message_length": len(message),
                "response_length": len(response_content)
            }
        
        except Exception as e:
            logger.error(f"Error processing chat for user {user_id}: {e}")
            return {
                "response": f"I encountered an error while processing your request. Please try again or contact support if the issue persists.",
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        #     # Get or create user-specific agent
        #     agent = self.get_or_create_agent(user_id)
            
        #     # Set session ID if provided, otherwise use existing or generate new
        #     if session_id:
        #         agent.session_id = session_id
        #     elif not hasattr(agent, 'session_id') or not agent.session_id:
        #         # Generate a session ID if not provided and doesn't exist
        #         agent.session_id = f"session_{user_id}_{uuid.uuid4().hex[:8]}"
            
        #     logger.info(f"Using session ID: {agent.session_id}")
            
        #     # Process the message with better error handling
        #     try:
        #         response = agent.run(message)
        #     except Exception as agent_error:
        #         logger.error(f"Error running agent for user {user_id}: {agent_error}")
        #         return {
        #             "response": "I encountered an error while processing your request. Please try again.",
        #             "success": False,
        #             "error": f"Agent error: {str(agent_error)}",
        #             "user_id": user_id,
        #             "session_id": agent.session_id,
        #             "timestamp": datetime.utcnow().isoformat()
        #         }
            
        #     # Extract response content
        #     if hasattr(response, 'content'):
        #         response_content = response.content
        #     else:
        #         response_content = str(response)
            
        #     logger.info(f"Generated response for user {user_id}")
            
        #     # Return structured response
        #     return {
        #         "response": response_content,
        #         "success": True,
        #         "session_id": agent.session_id,
        #         "user_id": user_id,
        #         "timestamp": datetime.utcnow().isoformat(),
        #         "message_length": len(message),
        #         "response_length": len(response_content)
        #     }
            
        # except Exception as e:
        #     logger.error(f"Error processing chat for user {user_id}: {e}")
        #     return {
        #         "response": f"I encountered an error while processing your request. Please try again or contact support if the issue persists.",
        #         "success": False,
        #         "error": str(e),
        #         "user_id": user_id,
        #         "session_id": agent.session_id,
        #         "timestamp": datetime.utcnow().isoformat()
        #     }

    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all sessions for a user with error handling"""
        try:
            agent = self.get_or_create_agent(user_id)
            if hasattr(agent.storage, 'get_all_session_ids'):
                return agent.storage.get_all_session_ids(user_id)
            else:
                logger.warning(f"Storage doesn't support get_all_session_ids for user {user_id}")
                return []
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []

    def refresh_user_knowledge(self, user_id: str, force_refresh: bool = False) -> bool:
        """Refresh user's knowledge base with latest meeting data"""
        try:
            logger.info(f"Refreshing knowledge base for user {user_id} (force_refresh: {force_refresh})")
            
            if force_refresh:
                # Remove cached agent and knowledge base for complete refresh
                if user_id in self.agents:
                    del self.agents[user_id]
                    logger.info(f"Removed cached agent for user {user_id}")
                
                if user_id in self.knowledge_bases:
                    del self.knowledge_bases[user_id]
                    logger.info(f"Removed cached knowledge base for user {user_id}")
                
                # Clear processed meetings tracking for complete refresh
                if user_id in self.processed_meetings:
                    del self.processed_meetings[user_id]
                    logger.info(f"Cleared processed meetings tracking for user {user_id}")
                
                # Recreate knowledge base with all data
                knowledge_base = self.create_user_knowledge_base(user_id, force_refresh=True)
            else:
                # Just update incrementally
                if user_id in self.knowledge_bases:
                    self._update_knowledge_base_incrementally(user_id)
                else:
                    # Create new knowledge base
                    knowledge_base = self.create_user_knowledge_base(user_id)
            
            logger.info(f"Successfully refreshed knowledge base for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing knowledge base for user {user_id}: {e}")
            return False

    def get_agent_memory(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user's agent memory and conversation history"""
        try:
            agent = self.get_or_create_agent(user_id)
            
            memory_info = {
                'user_id': user_id,
                'session_id': session_id or getattr(agent, 'session_id', None),
                'memories': [],
                'summary': None,
                'session_count': len(self.get_user_sessions(user_id))
            }
            
            # Get memories if available
            if hasattr(agent.memory, 'get_memories'):
                try:
                    memories = agent.memory.get_memories(user_id=user_id, limit=50)
                    memory_info['memories'] = [
                        {
                            'content': memory.memory if hasattr(memory, 'memory') else str(memory),
                            'created_at': memory.created_at.isoformat() if hasattr(memory, 'created_at') else None
                        }
                        for memory in memories
                    ]
                except Exception as e:
                    logger.warning(f"Error getting memories for user {user_id}: {e}")
            
            # Get summary if available
            if hasattr(agent.memory, 'get_summary'):
                try:
                    summary = agent.memory.get_summary(user_id=user_id)
                    memory_info['summary'] = summary
                except Exception as e:
                    logger.warning(f"Error getting summary for user {user_id}: {e}")
            
            return memory_info
            
        except Exception as e:
            logger.error(f"Error getting agent memory for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'memories': [],
                'summary': None,
                'session_count': 0
            }

    def clear_user_data(self, user_id: str, clear_memories: bool = False) -> bool:
        """Clear cached data for a user with option to clear memories"""
        try:
            logger.info(f"Clearing cached data for user {user_id} (clear_memories: {clear_memories})")
            
            # Remove from caches
            if user_id in self.agents:
                if clear_memories and hasattr(self.agents[user_id], 'memory'):
                    try:
                        # Clear memories from database
                        memory_db = self.agents[user_id].memory.db
                        if hasattr(memory_db, 'clear_memories'):
                            memory_db.clear_memories(user_id=user_id)
                        logger.info(f"Cleared memories for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error clearing memories for user {user_id}: {e}")
                
                del self.agents[user_id]
            
            if user_id in self.knowledge_bases:
                del self.knowledge_bases[user_id]
            
            if user_id in self.processed_meetings:
                del self.processed_meetings[user_id]
            
            logger.info(f"Successfully cleared cached data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing user data for {user_id}: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the chatbot system"""
        try:
            health_status = {
                'mysql_connection': False,
                'postgres_connection': False,
                'openai_api': bool(OPENAI_API_KEY),
                'cached_agents': len(self.agents),
                'cached_knowledge_bases': len(self.knowledge_bases),
                'processed_meetings_tracking': len(self.processed_meetings),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Test MySQL connection
            try:
                with self.SessionLocal() as db:
                    db.execute(text("SELECT 1"))
                health_status['mysql_connection'] = True
            except Exception as e:
                logger.error(f"MySQL health check failed: {e}")
            
            # Test PostgreSQL connection
            try:
                import psycopg2
                from urllib.parse import urlparse
                parsed = urlparse(self.vector_db_url)
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path[1:]
                )
                conn.close()
                health_status['postgres_connection'] = True
            except Exception as e:
                logger.error(f"PostgreSQL health check failed: {e}")
            
            health_status['overall_health'] = all([
                health_status['mysql_connection'],
                health_status['postgres_connection'],
                health_status['openai_api']
            ])
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'overall_health': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_knowledge_base_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's knowledge base"""
        try:
            stats = {
                'user_id': user_id,
                'has_knowledge_base': user_id in self.knowledge_bases,
                'processed_meetings_count': len(self._get_processed_meetings(user_id)),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if user_id in self.knowledge_bases:
                kb = self.knowledge_bases[user_id]
                if hasattr(kb.vector_db, 'get_document_count'):
                    try:
                        stats['documents_in_kb'] = kb.vector_db.get_document_count()
                    except:
                        stats['documents_in_kb'] = 'unknown'
                else:
                    stats['documents_in_kb'] = 'unknown'
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting knowledge base stats for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }