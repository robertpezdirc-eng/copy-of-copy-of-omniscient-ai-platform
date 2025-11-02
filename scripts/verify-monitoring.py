#!/usr/bin/env python3
"""
Verify monitoring metrics are properly configured.
This script checks that all expected Prometheus metrics are defined.
"""
import sys
import importlib.util


def check_module_metrics(module_path, expected_metrics):
    """Check if a Python module defines expected metrics."""
    spec = importlib.util.spec_from_file_location("module", module_path)
    if spec is None or spec.loader is None:
        print(f"❌ Could not load module: {module_path}")
        return False
    
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"⚠️  Warning loading {module_path}: {e}")
        return False
    
    all_found = True
    for metric_name in expected_metrics:
        if hasattr(module, metric_name):
            print(f"✅ {metric_name} - found")
        else:
            print(f"❌ {metric_name} - NOT FOUND")
            all_found = False
    
    return all_found


def main():
    """Main verification function."""
    print("🔍 Verifying Monitoring Metrics Configuration\n")
    print("=" * 60)
    
    # Check cache metrics
    print("\n📊 Cache Metrics (gateway/app/response_cache.py):")
    cache_metrics = [
        "cache_hits_total",
        "cache_misses_total",
        "cache_size_gauge",
    ]
    cache_ok = check_module_metrics(
        "gateway/app/response_cache.py",
        cache_metrics
    )
    
    # Check Redis metrics
    print("\n📊 Redis Metrics (gateway/app/redis_metrics.py):")
    redis_metrics = [
        "redis_connected",
        "redis_memory_used_bytes",
        "redis_memory_peak_bytes",
        "redis_keys_total",
        "redis_connected_clients",
    ]
    redis_ok = check_module_metrics(
        "gateway/app/redis_metrics.py",
        redis_metrics
    )
    
    # Check business metrics
    print("\n📊 Business Metrics (gateway/app/business_metrics.py):")
    business_metrics = [
        "revenue_total",
        "active_users_gauge",
        "user_engagement_score",
        "model_accuracy_gauge",
        "model_inference_total",
        "model_prediction_latency",
    ]
    business_ok = check_module_metrics(
        "gateway/app/business_metrics.py",
        business_metrics
    )
    
    # Check HTTP metrics
    print("\n📊 HTTP Metrics (gateway/app/metrics.py):")
    http_metrics = [
        "REQUEST_COUNT",
        "REQUEST_LATENCY",
    ]
    http_ok = check_module_metrics(
        "gateway/app/metrics.py",
        http_metrics
    )
    
    # Check dashboards exist
    print("\n📊 Grafana Dashboards:")
    import os
    dashboards = [
        "dashboards/grafana-cache-monitoring.json",
        "dashboards/grafana-fastapi-monitoring.json",
        "dashboards/grafana-business-metrics.json",
    ]
    dashboards_ok = True
    for dashboard in dashboards:
        if os.path.exists(dashboard):
            print(f"✅ {dashboard}")
        else:
            print(f"❌ {dashboard} - NOT FOUND")
            dashboards_ok = False
    
    # Check monitoring configs
    print("\n📊 Monitoring Configurations:")
    configs = [
        "monitoring/prometheus.yml",
        "monitoring/prometheus-alerts.yml",
        "monitoring/alertmanager.yml",
        "docker-compose.monitoring.yml",
    ]
    configs_ok = True
    for config in configs:
        if os.path.exists(config):
            print(f"✅ {config}")
        else:
            print(f"❌ {config} - NOT FOUND")
            configs_ok = False
    
    # Check documentation
    print("\n📚 Documentation:")
    docs = [
        "dashboards/README-GRAFANA.md",
    ]
    docs_ok = True
    for doc in docs:
        if os.path.exists(doc):
            print(f"✅ {doc}")
        else:
            print(f"❌ {doc} - NOT FOUND")
            docs_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("\n📝 Summary:")
    
    all_ok = all([cache_ok, redis_ok, business_ok, http_ok, dashboards_ok, configs_ok, docs_ok])
    
    if all_ok:
        print("✅ All metrics and configurations verified successfully!")
        print("\n🎉 Monitoring setup is complete and ready to use.")
        print("\n📚 Next steps:")
        print("   1. Start services: docker-compose -f docker-compose.monitoring.yml up -d")
        print("   2. Access Grafana: http://localhost:3000 (admin/admin)")
        print("   3. Import dashboards from dashboards/ directory")
        print("   4. Check metrics: http://localhost:8081/metrics")
        return 0
    else:
        print("❌ Some metrics or configurations are missing.")
        print("   Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
