class SecurityService:
    def __init__(self):
        self.ip_blacklist = set()
        self.login_attempts = {}
        self.anomaly_threshold = 5
        self.session_storage = {}
        
    def add_to_blacklist(self, ip):
        """Add an IP address to the blacklist."""
        self.ip_blacklist.add(ip)

    def is_ip_blacklisted(self, ip):
        """Check if an IP address is blacklisted."""
        return ip in self.ip_blacklist
        
    def track_login_attempt(self, user):
        """Track login attempts for a user."""
        if user not in self.login_attempts:
            self.login_attempts[user] = 0
        self.login_attempts[user] += 1
        
        if self.login_attempts[user] > self.anomaly_threshold:
            self.anomaly_detection(user)

    def anomaly_detection(self, user):
        """Detect anomalies based on login attempts."""
        print(f"Anomaly detected for user: {user}")

    def create_session(self, user):
        """Create a session for a user."""
        session_id = f"session_{user}"
        self.session_storage[session_id] = user
        return session_id

    def end_session(self, session_id):
        """End a user's session."""
        if session_id in self.session_storage:
            del self.session_storage[session_id]

    def audit_log(self, action, user):
        """Log an action for auditing purposes."""
        print(f"Audit log - User: {user}, Action: {action}")