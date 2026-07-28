import time
import hmac
import hashlib
import secrets
import threading

def generate_auth_headers(token: str) -> dict:
    """Replay-attack korumalı kimlik doğrulama başlıkları üretir."""
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)  # 16 byte -> daha güçlü nonce
    
    # İmzalanacak mesaj: timestamp:nonce
    message = f"{timestamp}:{nonce}".encode('utf-8')
    secret = token.encode('utf-8')
    
    signature = hmac.new(secret, message, digestmod=hashlib.sha256).hexdigest()
    
    return {
        'X-Healer-Timestamp': timestamp,
        'X-Healer-Nonce': nonce,
        'X-Healer-Signature': signature
    }

_used_nonces: dict = {}
_used_nonces_lock = threading.Lock()  # Thread-safe nonce erişimi için

def verify_auth_headers(headers: dict, expected_token: str, max_age_seconds: int = 60) -> bool:
    """Sunucu tarafında gelen başlıkları (HMAC, Timestamp, Nonce) doğrular."""
    global _used_nonces
    timestamp = headers.get('X-Healer-Timestamp')
    nonce = headers.get('X-Healer-Nonce')
    signature = headers.get('X-Healer-Signature')
    
    if not timestamp or not nonce or not signature:
        return False
        
    try:
        ts_int = int(timestamp)
        now = int(time.time())
        if abs(now - ts_int) > max_age_seconds:
            return False
    except ValueError:
        return False
    
    message = f"{timestamp}:{nonce}".encode('utf-8')
    secret = expected_token.encode('utf-8')
    
    expected_signature = hmac.new(secret, message, digestmod=hashlib.sha256).hexdigest()
    
    if hmac.compare_digest(signature, expected_signature):
        # Thread-safe nonce kaydı ve bellek temizliği
        with _used_nonces_lock:
            _used_nonces = {k: v for k, v in _used_nonces.items() if now - v <= max_age_seconds}
            if nonce in _used_nonces:
                return False  # Lock içinde tekrar kontrol (TOCTOU önlemi)
            _used_nonces[nonce] = now
        return True
        
    return False
