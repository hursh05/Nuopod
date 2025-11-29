from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Import your chatbot class
from scripts.chatbot import FinanceChatbot
# Import your SQLAlchemy models
from db.models import Transaction, Customer, UserFinancialInsights, TransactionClassification
# Import your database configuration (adjust based on your setup)
# from database import get_database_url, get_vector_db_url

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
POSTGRES_DB_URL = os.getenv("DATABASE_URL")
VECTOR_DB_URL = os.getenv("DATABASE_URL")

# Global chatbot instance
chatbot_instance: Optional[FinanceChatbot] = None


def get_chatbot() -> FinanceChatbot:
    """Get or create chatbot instance"""
    global chatbot_instance
    
    if chatbot_instance is None:
        try:
            logger.info("Initializing FinanceChatbot...")
            chatbot_instance = FinanceChatbot(
                postgres_db_url=POSTGRES_DB_URL,
                transaction_model=Transaction,
                customer_model=Customer,
                insights_model=UserFinancialInsights, 
                classification_model=TransactionClassification
            )
            logger.info("FinanceChatbot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            raise
    
    return chatbot_instance


# Request/Response Models
class ChatRequest:
    def __init__(self, data: dict):
        self.user_id = data.get('user_id')
        self.message = data.get('message')
        self.session_id = data.get('session_id')
        
    def validate(self):
        if not self.user_id:
            raise ValueError("user_id is required")
        if not self.message:
            raise ValueError("message is required")
        return True


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        chatbot = get_chatbot()
        health_status = chatbot.health_check()
        
        return jsonify({
            "status": "healthy" if health_status.get('overall_health') else "unhealthy",
            "details": health_status
        }), 200 if health_status.get('overall_health') else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503


@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request body"
            }), 400
        
        # Validate request
        chat_req = ChatRequest(data)
        try:
            chat_req.validate()
        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
        
        # Get chatbot instance
        chatbot = get_chatbot()
        
        # Process chat
        logger.info(f"Processing chat request for user: {chat_req.user_id}")
        response = chatbot.chat(
            user_id=chat_req.user_id,
            message=chat_req.message,
            session_id=chat_req.session_id
        )
        
        # Return response
        status_code = 200 if response.get('success') else 500
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500


@app.route('/sessions/<user_id>', methods=['GET'])
def get_sessions(user_id: str):
    """Get all sessions for a user"""
    try:
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        chatbot = get_chatbot()
        sessions = chatbot.get_user_sessions(user_id)
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "sessions": sessions,
            "count": len(sessions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/memory/<user_id>', methods=['GET'])
def get_memory(user_id: str):
    """Get user's agent memory"""
    try:
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        session_id = request.args.get('session_id')
        
        chatbot = get_chatbot()
        memory_info = chatbot.get_agent_memory(user_id, session_id)
        
        return jsonify({
            "success": True,
            "data": memory_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/knowledge/refresh', methods=['POST'])
def refresh_knowledge():
    """Refresh user's knowledge base"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        user_id = data['user_id']
        force_refresh = data.get('force_refresh', False)
        
        chatbot = get_chatbot()
        success = chatbot.refresh_user_knowledge(user_id, force_refresh)
        
        return jsonify({
            "success": success,
            "user_id": user_id,
            "force_refresh": force_refresh,
            "message": "Knowledge base refreshed successfully" if success else "Failed to refresh knowledge base"
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error refreshing knowledge: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/knowledge/stats/<user_id>', methods=['GET'])
def get_knowledge_stats(user_id: str):
    """Get knowledge base statistics"""
    try:
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        chatbot = get_chatbot()
        stats = chatbot.get_knowledge_base_stats(user_id)
        
        return jsonify({
            "success": True,
            "data": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/user/clear', methods=['POST'])
def clear_user_data():
    """Clear cached user data"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        user_id = data['user_id']
        clear_memories = data.get('clear_memories', False)
        
        chatbot = get_chatbot()
        success = chatbot.clear_user_data(user_id, clear_memories)
        
        return jsonify({
            "success": success,
            "user_id": user_id,
            "clear_memories": clear_memories,
            "message": "User data cleared successfully" if success else "Failed to clear user data"
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error clearing user data: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/transactions/<user_id>', methods=['GET'])
def get_user_transactions(user_id: str):
    """Get user transactions (direct database access)"""
    try:
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        transaction_type = request.args.get('type')
        
        chatbot = get_chatbot()
        
        # Create the tool and call it
        tools = chatbot.create_finance_tools(user_id)
        get_transactions_tool = tools[0]  # First tool is get_user_transactions
        
        result = get_transactions_tool(
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            category=category,
            transaction_type=transaction_type
        )
        
        import json
        return jsonify({
            "success": True,
            "data": json.loads(result)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/insights/<user_id>', methods=['GET'])
def get_user_insights(user_id: str):
    """Get user financial insights"""
    try:
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        chatbot = get_chatbot()
        
        # Create the tool and call it
        tools = chatbot.create_finance_tools(user_id)
        get_insights_tool = tools[3]  # Fourth tool is get_financial_insights
        
        result = get_insights_tool(user_id)
        
        import json
        return jsonify({
            "success": True,
            "data": json.loads(result)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/spending/category/<user_id>', methods=['GET'])
def get_spending_by_category(user_id: str):
    """Get spending breakdown by category"""
    try:
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        days = request.args.get('days', 30, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        chatbot = get_chatbot()
        
        # Create the tool and call it
        tools = chatbot.create_finance_tools(user_id)
        get_spending_tool = tools[1]  # Second tool is get_spending_by_category
        
        result = get_spending_tool(
            days=days,
            start_date=start_date,
            end_date=end_date
        )
        
        import json
        return jsonify({
            "success": True,
            "data": json.loads(result)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting spending: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/income/<user_id>', methods=['GET'])
def get_income_analysis(user_id: str):
    """Get income analysis"""
    try:
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        days = request.args.get('days', 30, type=int)
        
        chatbot = get_chatbot()
        
        # Create the tool and call it
        tools = chatbot.create_finance_tools(user_id)
        get_income_tool = tools[2]  # Third tool is get_income_analysis
        
        result = get_income_tool(days=days)
        
        import json
        return jsonify({
            "success": True,
            "data": json.loads(result)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting income analysis: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    # Development server
    app.run(
        port=5000,
        debug=True  # Set to False in production
    )