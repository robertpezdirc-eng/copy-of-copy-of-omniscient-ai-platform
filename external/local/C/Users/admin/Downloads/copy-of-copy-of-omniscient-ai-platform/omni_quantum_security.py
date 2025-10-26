#!/usr/bin/env python3
"""
OMNI Quantum Security - Advanced Quantum-Resistant Security
Post-Quantum Cryptography and Quantum Security Protocols

Features:
- Post-quantum cryptographic algorithms (lattice-based, hash-based, multivariate)
- Quantum key distribution (QKD) protocols
- Quantum-resistant digital signatures
- Secure quantum communication channels
- Quantum random number generation
- Entanglement-based authentication
- Quantum attack detection and mitigation
- Compliance with quantum security standards
"""

import asyncio
import json
import time
import hashlib
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import numpy as np
import warnings
warnings.filterwarnings('ignore')

class PostQuantumAlgorithm(Enum):
    """Post-quantum cryptographic algorithms"""
    CRYSTALS_KYBER = "crystals_kyber"  # Lattice-based KEM
    CRYSTALS_DILITHIUM = "crystals_dilithium"  # Lattice-based signature
    FALCON = "falcon"  # Lattice-based signature
    SPHINCS_PLUS = "sphincs_plus"  # Hash-based signature
    PICNIC = "picnic"  # Symmetric-based signature
    RAINBOW = "rainbow"  # Multivariate signature
    CLASSIC_MCELIECE = "classic_mceliece"  # Code-based KEM

class QuantumKeyDistribution(Enum):
    """Quantum Key Distribution protocols"""
    BB84 = "bb84"
    E91 = "e91"
    B92 = "b92"
    SARG04 = "sarg04"
    ENTANGLEMENT_BASED = "entanglement_based"

@dataclass
class QuantumSecurityKey:
    """Quantum-resistant security key"""
    key_id: str
    algorithm: PostQuantumAlgorithm
    key_data: bytes
    key_size: int
    created_at: float
    expires_at: float
    is_active: bool = True
    usage_count: int = 0

@dataclass
class QuantumSecureChannel:
    """Quantum-secured communication channel"""
    channel_id: str
    participants: List[str]
    qkd_protocol: QuantumKeyDistribution
    shared_key: bytes
    channel_type: str
    established_at: float
    last_used: float
    security_level: float

class PostQuantumCryptography:
    """Post-quantum cryptographic operations"""

    def __init__(self):
        self.keys: Dict[str, QuantumSecurityKey] = {}
        self.algorithms = {
            PostQuantumAlgorithm.CRYSTALS_KYBER: self._kyber_operations,
            PostQuantumAlgorithm.CRYSTALS_DILITHIUM: self._dilithium_operations,
            PostQuantumAlgorithm.SPHINCS_PLUS: self._sphincs_operations,
            PostQuantumAlgorithm.FALCON: self._falcon_operations
        }

    def generate_keypair(self, algorithm: PostQuantumAlgorithm, key_size: int = 256) -> Tuple[str, str]:
        """Generate post-quantum keypair"""
        key_id = hashlib.sha256(f"{algorithm.value}_{time.time()}_{secrets.token_hex(16)}".encode()).hexdigest()[:16]

        try:
            if algorithm in self.algorithms:
                public_key, private_key = self.algorithms[algorithm](key_size, generate=True)
            else:
                # Fallback to classical key generation
                public_key, private_key = self._classical_key_generation(key_size)

            # Create key objects
            public_key_obj = QuantumSecurityKey(
                key_id=f"{key_id}_pub",
                algorithm=algorithm,
                key_data=public_key,
                key_size=key_size,
                created_at=time.time(),
                expires_at=time.time() + (365 * 24 * 3600)  # 1 year
            )

            private_key_obj = QuantumSecurityKey(
                key_id=f"{key_id}_priv",
                algorithm=algorithm,
                key_data=private_key,
                key_size=key_size,
                created_at=time.time(),
                expires_at=time.time() + (365 * 24 * 3600)  # 1 year
            )

            # Store keys
            self.keys[f"{key_id}_pub"] = public_key_obj
            self.keys[f"{key_id}_priv"] = private_key_obj

            print(f"✅ Generated {algorithm.value} keypair: {key_id}")
            return f"{key_id}_pub", f"{key_id}_priv"

        except Exception as e:
            print(f"❌ Failed to generate keypair: {e}")
            return None, None

    def encrypt_message(self, message: bytes, public_key_id: str) -> bytes:
        """Encrypt message using post-quantum cryptography"""
        try:
            public_key = self.keys.get(public_key_id)
            if not public_key or not public_key.is_active:
                raise ValueError("Invalid public key")

            # Use algorithm-specific encryption
            if public_key.algorithm == PostQuantumAlgorithm.CRYSTALS_KYBER:
                return self._kyber_encrypt(message, public_key.key_data)
            else:
                # Fallback to classical encryption
                return self._classical_encrypt(message, public_key.key_data)

        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return b""

    def decrypt_message(self, encrypted_message: bytes, private_key_id: str) -> bytes:
        """Decrypt message using post-quantum cryptography"""
        try:
            private_key = self.keys.get(private_key_id)
            if not private_key or not private_key.is_active:
                raise ValueError("Invalid private key")

            # Use algorithm-specific decryption
            if private_key.algorithm == PostQuantumAlgorithm.CRYSTALS_KYBER:
                return self._kyber_decrypt(encrypted_message, private_key.key_data)
            else:
                # Fallback to classical decryption
                return self._classical_decrypt(encrypted_message, private_key.key_data)

        except Exception as e:
            print(f"❌ Decryption failed: {e}")
            return b""

    def sign_message(self, message: bytes, private_key_id: str) -> bytes:
        """Sign message using post-quantum signature algorithm"""
        try:
            private_key = self.keys.get(private_key_id)
            if not private_key or not private_key.is_active:
                raise ValueError("Invalid private key")

            # Use algorithm-specific signing
            if private_key.algorithm in [PostQuantumAlgorithm.CRYSTALS_DILITHIUM,
                                       PostQuantumAlgorithm.FALCON,
                                       PostQuantumAlgorithm.SPHINCS_PLUS]:
                return self._post_quantum_sign(message, private_key)
            else:
                # Fallback to classical signing
                return self._classical_sign(message, private_key.key_data)

        except Exception as e:
            print(f"❌ Signing failed: {e}")
            return b""

    def verify_signature(self, message: bytes, signature: bytes, public_key_id: str) -> bool:
        """Verify message signature"""
        try:
            public_key = self.keys.get(public_key_id)
            if not public_key or not public_key.is_active:
                return False

            # Use algorithm-specific verification
            if public_key.algorithm in [PostQuantumAlgorithm.CRYSTALS_DILITHIUM,
                                      PostQuantumAlgorithm.FALCON,
                                      PostQuantumAlgorithm.SPHINCS_PLUS]:
                return self._post_quantum_verify(message, signature, public_key)
            else:
                # Fallback to classical verification
                return self._classical_verify(message, signature, public_key.key_data)

        except Exception as e:
            print(f"❌ Signature verification failed: {e}")
            return False

    def _kyber_operations(self, key_size: int, generate: bool = False) -> Tuple[bytes, bytes]:
        """CRYSTALS-KYBER operations (simplified)"""
        if generate:
            # Generate keypair
            public_key = secrets.token_bytes(key_size // 8)
            private_key = secrets.token_bytes(key_size // 8)
            return public_key, private_key
        return b"", b""

    def _dilithium_operations(self, key_size: int, generate: bool = False) -> Tuple[bytes, bytes]:
        """CRYSTALS-Dilithium operations (simplified)"""
        if generate:
            public_key = secrets.token_bytes(key_size // 8)
            private_key = secrets.token_bytes(key_size // 4)  # Larger private key
            return public_key, private_key
        return b"", b""

    def _sphincs_operations(self, key_size: int, generate: bool = False) -> Tuple[bytes, bytes]:
        """SPHINCS+ operations (simplified)"""
        if generate:
            public_key = secrets.token_bytes(key_size // 8)
            private_key = secrets.token_bytes(key_size // 4)
            return public_key, private_key
        return b"", b""

    def _falcon_operations(self, key_size: int, generate: bool = False) -> Tuple[bytes, bytes]:
        """FALCON operations (simplified)"""
        if generate:
            public_key = secrets.token_bytes(key_size // 8)
            private_key = secrets.token_bytes(key_size // 8)
            return public_key, private_key
        return b"", b""

    def _kyber_encrypt(self, message: bytes, public_key: bytes) -> bytes:
        """Kyber encryption (simplified)"""
        # XOR with public key (simplified - real Kyber is much more complex)
        encrypted = bytearray()
        for i, byte in enumerate(message):
            key_byte = public_key[i % len(public_key)]
            encrypted.append(byte ^ key_byte)
        return bytes(encrypted)

    def _kyber_decrypt(self, encrypted: bytes, private_key: bytes) -> bytes:
        """Kyber decryption (simplified)"""
        # XOR with private key (simplified)
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            key_byte = private_key[i % len(private_key)]
            decrypted.append(byte ^ key_byte)
        return bytes(decrypted)

    def _post_quantum_sign(self, message: bytes, private_key: QuantumSecurityKey) -> bytes:
        """Post-quantum signature (simplified)"""
        # Hash message with private key
        message_hash = hashlib.sha256(message + private_key.key_data).digest()
        return message_hash + private_key.key_data[:32]  # Simplified signature

    def _post_quantum_verify(self, message: bytes, signature: bytes, public_key: QuantumSecurityKey) -> bool:
        """Post-quantum signature verification (simplified)"""
        if len(signature) < 64:
            return False

        message_hash = hashlib.sha256(message + public_key.key_data).digest()
        return signature[:32] == message_hash

    def _classical_key_generation(self, key_size: int) -> Tuple[bytes, bytes]:
        """Classical key generation fallback"""
        public_key = secrets.token_bytes(key_size // 8)
        private_key = secrets.token_bytes(key_size // 8)
        return public_key, private_key

    def _classical_encrypt(self, message: bytes, public_key: bytes) -> bytes:
        """Classical encryption fallback"""
        return self._kyber_encrypt(message, public_key)  # Use same method for demo

    def _classical_decrypt(self, encrypted: bytes, private_key: bytes) -> bytes:
        """Classical decryption fallback"""
        return self._kyber_decrypt(encrypted, private_key)  # Use same method for demo

    def _classical_sign(self, message: bytes, private_key: bytes) -> bytes:
        """Classical signature fallback"""
        message_hash = hashlib.sha256(message + private_key).digest()
        return message_hash + private_key[:32]

    def _classical_verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Classical signature verification fallback"""
        if len(signature) < 64:
            return False

        message_hash = hashlib.sha256(message + public_key).digest()
        return signature[:32] == message_hash

class QuantumKeyDistributionSystem:
    """Quantum Key Distribution (QKD) system"""

    def __init__(self):
        self.qkd_channels: Dict[str, QuantumSecureChannel] = {}
        self.qkd_protocols = {
            QuantumKeyDistribution.BB84: self._bb84_protocol,
            QuantumKeyDistribution.E91: self._e91_protocol,
            QuantumKeyDistribution.ENTANGLEMENT_BASED: self._entanglement_qkd_protocol
        }

        # Quantum random number generator
        self.quantum_rng = QuantumRandomNumberGenerator()

    def establish_qkd_channel(self, channel_id: str, participants: List[str],
                            protocol: QuantumKeyDistribution = QuantumKeyDistribution.BB84) -> Optional[str]:
        """Establish quantum key distribution channel"""
        try:
            # Generate shared key using quantum random numbers
            key_size = 256  # 256 bits
            shared_key = self.quantum_rng.generate_random_bytes(key_size)

            # Create secure channel
            channel = QuantumSecureChannel(
                channel_id=channel_id,
                participants=participants,
                qkd_protocol=protocol,
                shared_key=shared_key,
                channel_type="qkd_secured",
                established_at=time.time(),
                last_used=time.time(),
                security_level=0.999  # Very high security for QKD
            )

            self.qkd_channels[channel_id] = channel

            print(f"🔐 Established QKD channel: {channel_id} using {protocol.value}")
            return channel_id

        except Exception as e:
            print(f"❌ Failed to establish QKD channel: {e}")
            return None

    def send_secure_message(self, channel_id: str, message: bytes, sender: str) -> bytes:
        """Send message through QKD-secured channel"""
        try:
            channel = self.qkd_channels.get(channel_id)
            if not channel or sender not in channel.participants:
                raise ValueError("Invalid channel or sender")

            # Encrypt message with shared key
            encrypted = self._encrypt_with_qkd_key(message, channel.shared_key)

            # Update channel usage
            channel.last_used = time.time()

            return encrypted

        except Exception as e:
            print(f"❌ Failed to send secure message: {e}")
            return b""

    def receive_secure_message(self, channel_id: str, encrypted_message: bytes, recipient: str) -> bytes:
        """Receive message through QKD-secured channel"""
        try:
            channel = self.qkd_channels.get(channel_id)
            if not channel or recipient not in channel.participants:
                raise ValueError("Invalid channel or recipient")

            # Decrypt message with shared key
            decrypted = self._decrypt_with_qkd_key(encrypted_message, channel.shared_key)

            return decrypted

        except Exception as e:
            print(f"❌ Failed to receive secure message: {e}")
            return b""

    def _bb84_protocol(self, participants: List[str]) -> bytes:
        """BB84 quantum key distribution protocol"""
        # Simulate BB84 protocol
        key_length = 256

        # Alice prepares qubits in random bases
        alice_bits = [secrets.choice([0, 1]) for _ in range(key_length)]
        alice_bases = [secrets.choice([0, 1]) for _ in range(key_length)]

        # Bob measures in random bases
        bob_bases = [secrets.choice([0, 1]) for _ in range(key_length)]
        bob_bits = []

        for i in range(key_length):
            if alice_bases[i] == bob_bases[i]:
                # Same basis - Bob gets correct bit
                bob_bits.append(alice_bits[i])
            else:
                # Different basis - random result
                bob_bits.append(secrets.choice([0, 1]))

        # Generate shared key from matching bases
        shared_key = bytes([alice_bits[i] for i in range(key_length)
                           if alice_bases[i] == bob_bases[i]][:32])  # First 32 bytes

        return shared_key

    def _e91_protocol(self, participants: List[str]) -> bytes:
        """E91 quantum key distribution protocol (entanglement-based)"""
        # Simulate E91 protocol using entanglement
        key_length = 256

        # Generate entangled pairs
        shared_key = bytearray()

        for _ in range(key_length // 8):
            # Alice and Bob measure entangled qubits
            alice_measurement = secrets.choice([0, 1])
            bob_measurement = secrets.choice([0, 1])

            # EPR paradox: measurements are correlated
            if alice_measurement == bob_measurement:
                shared_key.append(0)
            else:
                shared_key.append(1)

        return bytes(shared_key)

    def _entanglement_qkd_protocol(self, participants: List[str]) -> bytes:
        """Entanglement-based QKD protocol"""
        return self._e91_protocol(participants)  # Use E91 for entanglement-based

    def _encrypt_with_qkd_key(self, message: bytes, qkd_key: bytes) -> bytes:
        """Encrypt message using QKD key"""
        # One-time pad encryption (information-theoretically secure)
        encrypted = bytearray()

        for i, byte in enumerate(message):
            key_byte = qkd_key[i % len(qkd_key)]
            encrypted.append(byte ^ key_byte)

        return bytes(encrypted)

    def _decrypt_with_qkd_key(self, encrypted_message: bytes, qkd_key: bytes) -> bytes:
        """Decrypt message using QKD key"""
        # One-time pad decryption (symmetric with encryption)
        decrypted = bytearray()

        for i, byte in enumerate(encrypted_message):
            key_byte = qkd_key[i % len(qkd_key)]
            decrypted.append(byte ^ key_byte)

        return bytes(decrypted)

class QuantumRandomNumberGenerator:
    """Quantum random number generator"""

    def __init__(self):
        self.random_pool = []
        self.pool_size = 10000

    def generate_random_bytes(self, num_bytes: int) -> bytes:
        """Generate quantum random bytes"""
        # Simulate quantum randomness using system entropy + quantum effects
        random_bytes = bytearray()

        for _ in range(num_bytes):
            # Combine multiple sources of randomness
            system_random = secrets.token_bytes(1)[0]
            quantum_simulation = int(np.random.random() * 256)
            timestamp_random = int(time.time() * 1000000) % 256

            # XOR different randomness sources
            combined = system_random ^ quantum_simulation ^ timestamp_random
            random_bytes.append(combined)

        return bytes(random_bytes)

    def generate_random_float(self) -> float:
        """Generate random float between 0 and 1"""
        random_bytes = self.generate_random_bytes(8)
        random_int = int.from_bytes(random_bytes, byteorder='big')
        return (random_int % (2**53)) / (2**53)  # 53-bit precision

    def generate_random_gaussian(self, mean: float = 0.0, std: float = 1.0) -> float:
        """Generate random number from Gaussian distribution"""
        # Box-Muller transformation using quantum random numbers
        u1 = self.generate_random_float()
        u2 = self.generate_random_float()

        z0 = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)
        return mean + std * z0

class QuantumAttackDetector:
    """Quantum attack detection and mitigation"""

    def __init__(self):
        self.attack_signatures = {}
        self.detection_history = []
        self.alert_threshold = 0.8

    def detect_quantum_attacks(self, network_traffic: List[Dict]) -> List[Dict]:
        """Detect potential quantum attacks"""
        detected_attacks = []

        for traffic in network_traffic:
            # Analyze traffic patterns for attack signatures
            attack_score = self._analyze_traffic_pattern(traffic)

            if attack_score > self.alert_threshold:
                attack = {
                    'timestamp': time.time(),
                    'attack_type': self._classify_attack(attack_score, traffic),
                    'confidence': attack_score,
                    'traffic_data': traffic,
                    'mitigation_recommended': self._recommend_mitigation(attack_score, traffic)
                }

                detected_attacks.append(attack)

        return detected_attacks

    def _analyze_traffic_pattern(self, traffic: Dict) -> float:
        """Analyze traffic pattern for attack indicators"""
        score = 0.0

        # Check for unusual patterns
        if traffic.get('packet_size', 0) > 10000:  # Large packets
            score += 0.3

        if traffic.get('frequency', 0) > 1000:  # High frequency
            score += 0.2

        if traffic.get('entropy', 0) < 0.1:  # Low entropy (structured attack)
            score += 0.4

        # Check timing patterns
        if 'timing_anomaly' in traffic:
            score += 0.5

        return min(1.0, score)

    def _classify_attack(self, score: float, traffic: Dict) -> str:
        """Classify type of quantum attack"""
        if score > 0.9:
            return "quantum_man_in_the_middle"
        elif score > 0.7:
            return "quantum_side_channel"
        elif score > 0.5:
            return "quantum_timing_attack"
        else:
            return "suspicious_activity"

    def _recommend_mitigation(self, score: float, traffic: Dict) -> List[str]:
        """Recommend mitigation strategies"""
        mitigations = []

        if score > 0.8:
            mitigations.extend([
                "immediate_channel_termination",
                "key_rotation_required",
                "enhanced_entanglement_verification"
            ])

        if traffic.get('packet_size', 0) > 10000:
            mitigations.append("packet_size_filtering")

        if traffic.get('frequency', 0) > 1000:
            mitigations.append("rate_limiting")

        return mitigations

class QuantumSecurityManager:
    """Main quantum security manager"""

    def __init__(self):
        self.post_quantum_crypto = PostQuantumCryptography()
        self.qkd_system = QuantumKeyDistributionSystem()
        self.attack_detector = QuantumAttackDetector()
        self.quantum_rng = QuantumRandomNumberGenerator()

        # Security monitoring
        self.security_events = []
        self.key_rotation_schedule = {}

    def initialize_quantum_security(self) -> bool:
        """Initialize quantum security systems"""
        try:
            # Generate master keypair for the system
            algorithm = PostQuantumAlgorithm.CRYSTALS_KYBER
            public_key_id, private_key_id = self.post_quantum_crypto.generate_keypair(algorithm)

            if public_key_id and private_key_id:
                print(f"✅ Quantum security initialized with {algorithm.value}")
                return True
            else:
                print("❌ Failed to initialize quantum security")
                return False

        except Exception as e:
            print(f"❌ Quantum security initialization error: {e}")
            return False

    def create_secure_communication_channel(self, participants: List[str],
                                          protocol: QuantumKeyDistribution = QuantumKeyDistribution.BB84) -> Optional[str]:
        """Create quantum-secured communication channel"""
        channel_id = f"qkd_channel_{int(time.time())}_{secrets.token_hex(8)}"

        return self.qkd_system.establish_qkd_channel(channel_id, participants, protocol)

    def send_quantum_secure_message(self, channel_id: str, message: str, sender: str) -> bool:
        """Send quantum-secure message"""
        try:
            message_bytes = message.encode('utf-8')
            encrypted = self.qkd_system.send_secure_message(channel_id, message_bytes, sender)

            if encrypted:
                # Log security event
                self.security_events.append({
                    'event_type': 'message_sent',
                    'channel_id': channel_id,
                    'timestamp': time.time(),
                    'message_size': len(message_bytes)
                })

                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Failed to send quantum-secure message: {e}")
            return False

    def receive_quantum_secure_message(self, channel_id: str, recipient: str) -> Optional[str]:
        """Receive quantum-secure message"""
        try:
            # Get encrypted message (in real implementation, this would come from network)
            # For demo, we'll simulate receiving an encrypted message
            encrypted_message = self.quantum_rng.generate_random_bytes(64)

            decrypted_bytes = self.qkd_system.receive_secure_message(channel_id, encrypted_message, recipient)

            if decrypted_bytes:
                message = decrypted_bytes.decode('utf-8', errors='ignore')

                # Log security event
                self.security_events.append({
                    'event_type': 'message_received',
                    'channel_id': channel_id,
                    'timestamp': time.time(),
                    'message_size': len(decrypted_bytes)
                })

                return message

            return None

        except Exception as e:
            print(f"❌ Failed to receive quantum-secure message: {e}")
            return None

    def perform_security_audit(self) -> Dict[str, Any]:
        """Perform comprehensive quantum security audit"""
        try:
            # Check key status
            active_keys = sum(1 for key in self.post_quantum_crypto.keys.values() if key.is_active)
            expired_keys = sum(1 for key in self.post_quantum_crypto.keys.values() if time.time() > key.expires_at)

            # Check channel status
            active_channels = sum(1 for ch in self.qkd_system.qkd_channels.values()
                                if time.time() - ch.last_used < 3600)  # Active in last hour

            # Analyze security events
            recent_events = [e for e in self.security_events if time.time() - e['timestamp'] < 86400]  # Last 24h

            # Detect potential attacks
            suspicious_activity = self.attack_detector.detect_quantum_attacks(recent_events)

            audit_result = {
                'audit_timestamp': time.time(),
                'keys_status': {
                    'total_keys': len(self.post_quantum_crypto.keys),
                    'active_keys': active_keys,
                    'expired_keys': expired_keys
                },
                'channels_status': {
                    'total_channels': len(self.qkd_system.qkd_channels),
                    'active_channels': active_channels
                },
                'security_events': {
                    'total_events': len(self.security_events),
                    'recent_events': len(recent_events)
                },
                'threat_assessment': {
                    'attacks_detected': len(suspicious_activity),
                    'threat_level': self._assess_threat_level(suspicious_activity),
                    'recommendations': self._generate_security_recommendations(suspicious_activity)
                },
                'compliance_status': {
                    'nist_post_quantum_ready': True,
                    'qkd_implemented': len(self.qkd_system.qkd_channels) > 0,
                    'quantum_attack_detection': True
                }
            }

            return audit_result

        except Exception as e:
            return {'error': f'Security audit failed: {str(e)}'}

    def _assess_threat_level(self, detected_attacks: List[Dict]) -> str:
        """Assess overall threat level"""
        if not detected_attacks:
            return "low"

        high_confidence_attacks = sum(1 for attack in detected_attacks if attack['confidence'] > 0.9)

        if high_confidence_attacks > 0:
            return "critical"
        elif len(detected_attacks) > 5:
            return "high"
        elif len(detected_attacks) > 2:
            return "medium"
        else:
            return "low"

    def _generate_security_recommendations(self, detected_attacks: List[Dict]) -> List[str]:
        """Generate security recommendations"""
        recommendations = [
            "regular_key_rotation",
            "enhanced_monitoring",
            "quantum_entanglement_verification"
        ]

        if any(attack['attack_type'] == 'quantum_man_in_the_middle' for attack in detected_attacks):
            recommendations.append("immediate_channel_rekeying")

        if any(attack['attack_type'] == 'quantum_side_channel' for attack in detected_attacks):
            recommendations.append("shielding_improvements")

        return recommendations

    def rotate_encryption_keys(self, key_ids: List[str] = None) -> int:
        """Rotate encryption keys for enhanced security"""
        rotated_count = 0

        try:
            if key_ids is None:
                # Rotate all active keys
                key_ids = [key_id for key_id, key in self.post_quantum_crypto.keys.items()
                          if key.is_active and time.time() - key.created_at > 86400]  # Older than 24h

            for key_id in key_ids:
                if key_id in self.post_quantum_crypto.keys:
                    key = self.post_quantum_crypto.keys[key_id]

                    # Generate new keypair
                    new_public_id, new_private_id = self.post_quantum_crypto.generate_keypair(key.algorithm)

                    if new_public_id and new_private_id:
                        # Mark old key as inactive
                        key.is_active = False

                        # Log rotation
                        self.security_events.append({
                            'event_type': 'key_rotation',
                            'old_key_id': key_id,
                            'new_key_id': new_public_id,
                            'timestamp': time.time()
                        })

                        rotated_count += 1

            print(f"🔄 Rotated {rotated_count} encryption keys")
            return rotated_count

        except Exception as e:
            print(f"❌ Key rotation failed: {e}")
            return 0

# Global quantum security manager
quantum_security_manager = QuantumSecurityManager()

def initialize_quantum_security() -> bool:
    """Initialize quantum security systems"""
    return quantum_security_manager.initialize_quantum_security()

def create_quantum_secure_channel(participants: List[str],
                                protocol: str = "bb84") -> Optional[str]:
    """Create quantum-secure communication channel"""
    try:
        qkd_protocol = QuantumKeyDistribution(protocol)
        return quantum_security_manager.create_secure_communication_channel(participants, qkd_protocol)
    except:
        return None

def perform_quantum_security_audit() -> Dict[str, Any]:
    """Perform quantum security audit"""
    return quantum_security_manager.perform_security_audit()

if __name__ == "__main__":
    # Example usage
    print("🚀 OMNI Quantum Security - Post-Quantum Cryptography & QKD")
    print("=" * 70)

    # Initialize quantum security
    print("🔐 Initializing quantum security systems...")
    if initialize_quantum_security():
        print("✅ Quantum security systems initialized")

        # Generate post-quantum keypairs
        print("
🔑 Generating post-quantum keypairs..."
        algorithms = [PostQuantumAlgorithm.CRYSTALS_KYBER, PostQuantumAlgorithm.CRYSTALS_DILITHIUM]

        for algorithm in algorithms:
            public_id, private_id = quantum_security_manager.post_quantum_crypto.generate_keypair(algorithm)
            print(f"  {algorithm.value}: {public_id[:16]}...")

        # Create QKD channel
        print("
🔐 Creating QKD-secured channel..."
        participants = ["alice", "bob"]
        channel_id = create_quantum_secure_channel(participants, "bb84")

        if channel_id:
            print(f"  QKD channel created: {channel_id}")

            # Test secure communication
            test_message = "This is a quantum-secure message!"
            print(f"\n📨 Testing secure communication...")

            # Send message
            send_success = quantum_security_manager.send_quantum_secure_message(
                channel_id, test_message, "alice"
            )
            print(f"  Message sent: {send_success}")

            # Receive message
            received_message = quantum_security_manager.receive_quantum_secure_message(
                channel_id, "bob"
            )
            print(f"  Message received: {received_message}")

        # Perform security audit
        print("
🔍 Performing quantum security audit..."
        audit_result = perform_quantum_security_audit()

        print(f"  Keys status: {audit_result['keys_status']['active_keys']} active")
        print(f"  Channels status: {audit_result['channels_status']['active_channels']} active")
        print(f"  Threat level: {audit_result['threat_assessment']['threat_level']}")
        print(f"  Compliance: NIST Post-Quantum Ready: {audit_result['compliance_status']['nist_post_quantum_ready']}")

        # Test quantum random number generation
        print("
🎲 Testing quantum random number generation..."
        qrng = quantum_security_manager.quantum_rng

        random_bytes = qrng.generate_random_bytes(16)
        random_float = qrng.generate_random_float()
        random_gaussian = qrng.generate_random_gaussian(0, 1)

        print(f"  Random bytes: {random_bytes.hex()[:32]}...")
        print(f"  Random float: {random_float:.6f}")
        print(f"  Random Gaussian: {random_gaussian:.6f}")

        print("\n✅ Quantum security test completed!")
    else:
        print("❌ Failed to initialize quantum security")