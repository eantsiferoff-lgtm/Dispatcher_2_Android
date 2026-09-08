import os

class ComposioGateway:
    """Only integration boundary. Domain skills never import Composio directly."""
    def __init__(self, user_id=None):
        self.user_id = user_id or os.getenv('DISPATCHER_USER_ID', 'user_001')
        self._composio = None
        self._session = None

    def _client(self):
        if self._composio is None:
            from composio import Composio
            api_key = os.getenv('COMPOSIO_API_KEY')
            if not api_key:
                raise RuntimeError('COMPOSIO_API_KEY is not set')
            self._composio = Composio(api_key=api_key)
        return self._composio

    def session(self):
        if self._session is None:
            self._session = self._client().sessions.create(user_id=self.user_id)
        return self._session

    def tools(self):
        return self.session().tools()

    def authorize(self, toolkit: str):
        connection_request = self.session().authorize(toolkit)
        return {'redirect_url': connection_request.redirect_url}

    def mcp_endpoint(self):
        session = self._client().sessions.create(user_id=self.user_id, mcp=True)
        return {'url': session.mcp.url, 'headers': session.mcp.headers, 'session_id': session.session_id}
