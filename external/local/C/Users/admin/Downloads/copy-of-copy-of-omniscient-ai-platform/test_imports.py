 
#!/usr/bin/env python3
"""Test script to check available imports"""

try:
    from omni_singularity_core import initialize_omni_singularity_core
    print('[OK] Quantum Singularity: Available')
except ImportError as e:
    print(f'[ERROR] Quantum Singularity: Not available - {e}')

try:
    from omni_real_api_integrations import omni_api_manager
    print('[OK] OpenAI Integration: Available')
except ImportError as e:
    print(f'[ERROR] OpenAI Integration: Not available - {e}')

try:
    from omni_quantum_cores import quantum_core_manager
    print('[OK] Quantum Cores: Available')
except ImportError as e:
    print(f'[ERROR] Quantum Cores: Not available - {e}')

try:
    from google.cloud import storage, monitoring_v3, pubsub_v1
    print('[OK] Google Cloud: Available')
except ImportError as e:
    print(f'[ERROR] Google Cloud: Not available - {e}')