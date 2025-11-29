const PROTOCOL = 'https';
const DOMAIN = 'madalynn-unhastened-vernacularly.ngrok-free.dev';
const SUFFIX = 'api';

const getBaseURL = () => {
  return `${PROTOCOL}://${DOMAIN}/${SUFFIX}`;
};

export { getBaseURL };
