"""Synthetic outage scenarios for Task 3: Multi-Service Outage Root Cause Analysis."""


def _ts(minute, second=0):
    return f"2026-04-04T14:{minute:02d}:{second:02d}Z"


SERVICE_TOPOLOGY = {
    "api-gateway": {"depends_on": ["auth-service", "user-service", "product-service"]},
    "auth-service": {"depends_on": ["user-db", "cache"]},
    "user-service": {"depends_on": ["user-db"]},
    "product-service": {"depends_on": ["product-db", "search-service"]},
    "payment-service": {"depends_on": ["payment-gateway", "queue"]},
    "queue": {"depends_on": []},
    "worker": {"depends_on": ["queue", "notification-service"]},
    "notification-service": {"depends_on": ["email-provider"]},
    "user-db": {"depends_on": []},
    "product-db": {"depends_on": []},
    "cache": {"depends_on": []},
    "search-service": {"depends_on": ["product-db"]},
    "payment-gateway": {"depends_on": []},
    "email-provider": {"depends_on": []},
}

# Default healthy metrics
_HEALTHY_METRICS = {
    "cpu": 25, "memory": 40, "latency_ms": 50, "error_rate": 0.01, "throughput": 200, "connections": 10,
}

# Default healthy config
_BASE_CONFIG = {
    "version": "2.3.0",
    "replicas": 3,
    "max_connections": 500,
    "timeout_ms": 5000,
    "log_level": "INFO",
}


SCENARIOS = [
    # ── Scenario 1: Database Connection Limit Exceeded ──
    {
        "id": "db_connection_limit",
        "description": "Users are reporting slow page loads and intermittent errors. The ops team has been alerted. Investigate the outage across all services.",
        "root_cause_service": "user-db",
        "root_cause_description_keywords": ["max_connections", "limit", "100", "exceeded", "connection", "postgres"],
        "failure_chain": ["user-db", "user-service", "auth-service", "api-gateway"],
        "remediation_steps": [
            "Increase max_connections on user-db from 100 to 500",
            "Restart user-service to clear stale connection pool",
            "Monitor auth-service recovery and cache hit rate",
            "Add PgBouncer connection pooling for long-term fix",
        ],
        "remediation_keywords": [
            ["increase", "max_connections", "500"],
            ["restart", "user-service", "connection"],
            ["monitor", "auth-service", "recovery"],
            ["pgbouncer", "pooling", "long-term"],
        ],
        "service_statuses": {
            "api-gateway": "degraded",
            "auth-service": "degraded",
            "user-service": "unhealthy",
            "user-db": "unhealthy",
            "product-service": "healthy",
            "product-db": "healthy",
            "search-service": "healthy",
            "payment-service": "healthy",
            "payment-gateway": "healthy",
            "queue": "healthy",
            "worker": "healthy",
            "notification-service": "healthy",
            "cache": "healthy",
            "email-provider": "healthy",
        },
        "service_metrics": {
            "user-db": {"cpu": 95, "memory": 82, "latency_ms": 5200, "error_rate": 0.85, "throughput": 15, "connections": 100},
            "user-service": {"cpu": 72, "memory": 65, "latency_ms": 4800, "error_rate": 0.70, "throughput": 30, "connections": 50},
            "auth-service": {"cpu": 48, "memory": 45, "latency_ms": 3500, "error_rate": 0.50, "throughput": 80, "connections": 40},
            "api-gateway": {"cpu": 55, "memory": 50, "latency_ms": 5000, "error_rate": 0.45, "throughput": 100, "connections": 200},
            "cache": {"cpu": 15, "memory": 60, "latency_ms": 5, "error_rate": 0.0, "throughput": 500, "connections": 30},
        },
        "service_logs": {
            "user-db": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "PostgreSQL 15.4 accepting connections"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "Connection count at 90/100 (max_connections=100)"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "FATAL: too many connections for role 'app_user' - max_connections=100 reached"},
                {"timestamp": _ts(2, 15), "level": "ERROR", "message": "FATAL: sorry, too many clients already (active: 100, max: 100)"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "Connection rejected: max_connections (100) exceeded, 35 clients in queue"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "FATAL: remaining connection slots reserved for superuser connections"},
                {"timestamp": _ts(3, 30), "level": "WARN", "message": "pg_stat_activity shows 100 active connections, 60 idle in transaction"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Service healthy, processing requests"},
                {"timestamp": _ts(1, 30), "level": "WARN", "message": "Database connection pool wait time: 3200ms (threshold: 1000ms)"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Cannot acquire connection from pool: all 50 connections in use, user-db rejecting new connections"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "Request failed: GET /users/123 - org.postgresql.util.PSQLException: FATAL: too many connections"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "Health check FAILED: database unreachable, returning 503"},
            ],
            "auth-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Token validation: 15ms avg"},
                {"timestamp": _ts(2, 0), "level": "WARN", "message": "Session lookup failing: upstream user-db connection refused"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "Cannot validate session: user-db connection pool exhausted at user-service"},
                {"timestamp": _ts(3, 0), "level": "WARN", "message": "Falling back to cache for session data (stale: 10min)"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Routing request to user-service"},
                {"timestamp": _ts(2, 0), "level": "WARN", "message": "user-service latency: 4800ms"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "user-service returned 503, auth-service returned 500"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "Circuit breaker OPEN for user-service after 10 consecutive 503s"},
            ],
        },
        "service_configs": {
            "user-db": {**_BASE_CONFIG, "version": "PostgreSQL 15.4", "max_connections": 100, "shared_buffers": "256MB", "work_mem": "4MB"},
            "user-service": {**_BASE_CONFIG, "pool_size": 50, "pool_timeout_ms": 5000},
            "auth-service": {**_BASE_CONFIG, "cache_ttl_seconds": 600, "fallback_enabled": True},
            "api-gateway": {**_BASE_CONFIG, "circuit_breaker_threshold": 10, "upstream_timeout_ms": 10000},
        },
        "traces": [
            {
                "trace_id": "trace-001",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 5100, "status": "error", "timestamp": _ts(2, 30)},
                    {"service": "auth-service", "operation": "validate_token", "duration_ms": 3500, "status": "error", "error": "session lookup failed - db unavailable", "timestamp": _ts(2, 30)},
                    {"service": "user-service", "operation": "get_user", "duration_ms": 4800, "status": "error", "error": "connection pool exhausted", "timestamp": _ts(2, 31)},
                    {"service": "user-db", "operation": "query", "duration_ms": 0, "status": "error", "error": "FATAL: too many connections (100/100)", "timestamp": _ts(2, 31)},
                ],
            },
            {
                "trace_id": "trace-002",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 150, "status": "ok", "timestamp": _ts(2, 32)},
                    {"service": "product-service", "operation": "get_products", "duration_ms": 45, "status": "ok", "timestamp": _ts(2, 32)},
                    {"service": "product-db", "operation": "query", "duration_ms": 12, "status": "ok", "timestamp": _ts(2, 32)},
                ],
            },
            {
                "trace_id": "trace-003",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 5050, "status": "error", "timestamp": _ts(3, 0)},
                    {"service": "user-service", "operation": "get_user", "duration_ms": 5000, "status": "error", "error": "timeout waiting for db connection", "timestamp": _ts(3, 0)},
                    {"service": "user-db", "operation": "connect", "duration_ms": 0, "status": "error", "error": "FATAL: too many clients already", "timestamp": _ts(3, 0)},
                ],
            },
        ],
        "alerts": [
            {"timestamp": _ts(1, 0), "service": "user-db", "severity": "warning", "message": "Connection count above 90% threshold"},
            {"timestamp": _ts(2, 0), "service": "user-db", "severity": "critical", "message": "Max connections reached (100/100)"},
            {"timestamp": _ts(2, 5), "service": "user-service", "severity": "critical", "message": "Health check failing"},
            {"timestamp": _ts(2, 10), "service": "auth-service", "severity": "warning", "message": "Error rate above 40%"},
            {"timestamp": _ts(2, 15), "service": "api-gateway", "severity": "critical", "message": "5xx error rate above 40%"},
        ],
    },

    # ── Scenario 2: Bad Deployment ──
    {
        "id": "bad_deploy",
        "description": "After a deployment 15 minutes ago, error rates have spiked across several services. The deploy has been flagged. Investigate and determine the root cause.",
        "root_cause_service": "payment-service",
        "root_cause_description_keywords": ["deploy", "v2.4.0", "payment", "serialization", "JSON", "breaking change"],
        "failure_chain": ["payment-service", "api-gateway", "worker"],
        "remediation_steps": [
            "Rollback payment-service from v2.4.0 to v2.3.0",
            "Drain and replay failed messages from the queue",
            "Verify worker processing resumes after rollback",
            "Add integration tests for payment API serialization format",
        ],
        "remediation_keywords": [
            ["rollback", "payment-service", "v2.3.0"],
            ["drain", "replay", "queue", "messages"],
            ["verify", "worker", "processing"],
            ["integration test", "serialization", "format"],
        ],
        "service_statuses": {
            "api-gateway": "degraded",
            "auth-service": "healthy",
            "user-service": "healthy",
            "user-db": "healthy",
            "product-service": "healthy",
            "product-db": "healthy",
            "search-service": "healthy",
            "payment-service": "unhealthy",
            "payment-gateway": "healthy",
            "queue": "degraded",
            "worker": "unhealthy",
            "notification-service": "healthy",
            "cache": "healthy",
            "email-provider": "healthy",
        },
        "service_metrics": {
            "payment-service": {"cpu": 80, "memory": 70, "latency_ms": 200, "error_rate": 0.92, "throughput": 5, "connections": 30},
            "api-gateway": {"cpu": 45, "memory": 42, "latency_ms": 1500, "error_rate": 0.35, "throughput": 150, "connections": 180},
            "queue": {"cpu": 30, "memory": 55, "latency_ms": 100, "error_rate": 0.0, "throughput": 500, "connections": 20},
            "worker": {"cpu": 85, "memory": 75, "latency_ms": 0, "error_rate": 0.88, "throughput": 2, "connections": 15},
        },
        "service_logs": {
            "payment-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Deployment v2.4.0 started, rolling update in progress"},
                {"timestamp": _ts(0, 30), "level": "INFO", "message": "Deployment v2.4.0 complete, all 3 replicas updated"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "message": "PaymentSerializer: cannot serialize amount field - expected float, got string in v2.4.0 response format"},
                {"timestamp": _ts(1, 15), "level": "ERROR", "message": "JSON serialization error: {'amount': '$49.99'} - breaking change in payment-gateway response parser v2.4.0"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "Payment processing failed: TypeError: unsupported operand type(s) for *: 'str' and 'float' in calculate_tax()"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "95% of payment requests failing since v2.4.0 deploy. Previous version v2.3.0 handled string-to-float conversion."},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "Dead letter queue growing: 450 failed payment events in 2 minutes"},
            ],
            "worker": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Worker consuming messages from payment queue"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "Failed to process payment event: malformed JSON from payment-service v2.4.0"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Message deserialization error: expected {amount: float, currency: str}, got {amount: str, currency: str}"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "Worker crash loop: 12 restarts in 5 minutes, all messages from payment-service v2.4.0 failing"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "Backpressure alert: 800 unprocessed messages in queue"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Routing requests normally"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "payment-service returning 500 for POST /api/payments"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Payment endpoint failure rate: 92%, returning 502 to clients"},
                {"timestamp": _ts(2, 30), "level": "WARN", "message": "Non-payment routes (users, products) operating normally"},
            ],
            "queue": [
                {"timestamp": _ts(1, 0), "level": "INFO", "message": "Queue depth: 50 messages (normal)"},
                {"timestamp": _ts(2, 0), "level": "WARN", "message": "Queue depth growing: 300 messages, consumer lag increasing"},
                {"timestamp": _ts(3, 0), "level": "WARN", "message": "Queue depth: 800 messages, dead letter queue: 450 messages"},
            ],
        },
        "service_configs": {
            "payment-service": {**_BASE_CONFIG, "version": "2.4.0", "previous_version": "2.3.0", "deployed_at": _ts(0, 0), "deployed_by": "ci-pipeline"},
            "worker": {**_BASE_CONFIG, "version": "2.3.0", "max_retries": 3, "retry_backoff_ms": 1000},
            "queue": {**_BASE_CONFIG, "version": "RabbitMQ 3.12", "max_queue_depth": 10000, "dead_letter_enabled": True},
            "api-gateway": {**_BASE_CONFIG},
        },
        "traces": [
            {
                "trace_id": "trace-101",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_payment", "duration_ms": 250, "status": "error", "timestamp": _ts(1, 30)},
                    {"service": "payment-service", "operation": "process_payment", "duration_ms": 50, "status": "error", "error": "TypeError: cannot serialize amount '$49.99' as float", "timestamp": _ts(1, 30)},
                ],
            },
            {
                "trace_id": "trace-102",
                "spans": [
                    {"service": "worker", "operation": "consume_message", "duration_ms": 10, "status": "error", "error": "malformed payment event from v2.4.0", "timestamp": _ts(2, 0)},
                    {"service": "queue", "operation": "nack_message", "duration_ms": 1, "status": "ok", "timestamp": _ts(2, 0)},
                ],
            },
            {
                "trace_id": "trace-103",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 60, "status": "ok", "timestamp": _ts(2, 15)},
                    {"service": "product-service", "operation": "get_products", "duration_ms": 30, "status": "ok", "timestamp": _ts(2, 15)},
                ],
            },
        ],
        "alerts": [
            {"timestamp": _ts(0, 30), "service": "payment-service", "severity": "info", "message": "Deployment v2.4.0 completed"},
            {"timestamp": _ts(1, 0), "service": "payment-service", "severity": "critical", "message": "Error rate above 90%"},
            {"timestamp": _ts(1, 15), "service": "worker", "severity": "critical", "message": "Consumer crash loop detected"},
            {"timestamp": _ts(2, 0), "service": "api-gateway", "severity": "warning", "message": "Payment endpoint 5xx rate above 30%"},
            {"timestamp": _ts(2, 30), "service": "queue", "severity": "warning", "message": "Queue depth exceeding threshold (800/10000)"},
        ],
    },

    # ── Scenario 3: Certificate Expiry Cascade ──
    {
        "id": "cert_expiry_cascade",
        "description": "Multiple services are reporting communication failures. Users cannot complete actions that require authentication. Investigate the cascading failure.",
        "root_cause_service": "cache",
        "root_cause_description_keywords": ["TLS", "certificate", "expired", "cache", "Redis", "mutual TLS"],
        "failure_chain": ["cache", "auth-service", "api-gateway"],
        "remediation_steps": [
            "Renew TLS certificate on cache (Redis) server",
            "Restart auth-service to re-establish TLS connections to cache",
            "Clear stale session data and verify auth flow end-to-end",
            "Set up certificate expiry monitoring with 30-day alert threshold",
        ],
        "remediation_keywords": [
            ["renew", "TLS", "certificate", "cache"],
            ["restart", "auth-service", "connection"],
            ["clear", "session", "verify"],
            ["monitoring", "expiry", "alert", "30-day"],
        ],
        "service_statuses": {
            "api-gateway": "degraded",
            "auth-service": "unhealthy",
            "user-service": "healthy",
            "user-db": "healthy",
            "product-service": "healthy",
            "product-db": "healthy",
            "search-service": "healthy",
            "payment-service": "healthy",
            "payment-gateway": "healthy",
            "queue": "healthy",
            "worker": "healthy",
            "notification-service": "healthy",
            "cache": "unhealthy",
            "email-provider": "healthy",
        },
        "service_metrics": {
            "cache": {"cpu": 10, "memory": 30, "latency_ms": 0, "error_rate": 1.0, "throughput": 0, "connections": 0},
            "auth-service": {"cpu": 60, "memory": 55, "latency_ms": 8000, "error_rate": 0.80, "throughput": 20, "connections": 5},
            "api-gateway": {"cpu": 50, "memory": 48, "latency_ms": 8500, "error_rate": 0.65, "throughput": 80, "connections": 200},
        },
        "service_logs": {
            "cache": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Redis 7.2 running with TLS enabled (mutual TLS required)"},
                {"timestamp": _ts(0, 10), "level": "WARN", "message": "TLS server certificate expires in 0 days: CN=cache.internal, notAfter=2026-04-03T23:59:59Z"},
                {"timestamp": _ts(0, 30), "level": "ERROR", "message": "TLS certificate EXPIRED: /etc/redis/tls/redis.crt expired at 2026-04-03T23:59:59Z"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "message": "Rejecting all TLS connections: certificate expired, clients receiving SSL_ERROR_EXPIRED_CERT_ALERT"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "0 active client connections (was 45), all TLS handshakes failing"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Auto-renewal failed: certbot returned error - ACME DNS challenge record missing"},
            ],
            "auth-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Session cache connected: redis://cache.internal:6379"},
                {"timestamp": _ts(0, 30), "level": "ERROR", "message": "Redis connection failed: SSL handshake error - peer certificate has expired"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "message": "Cannot read session from cache: TLS connection to cache.internal:6379 refused - certificate expired"},
                {"timestamp": _ts(1, 30), "level": "WARN", "message": "Falling back to database session lookup (10x slower)"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Session validation taking 8000ms (cache miss → DB fallback), auth requests timing out"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "80% of auth requests failing: cache unavailable, DB fallback overloaded"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Normal operation, routing requests"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "auth-service latency spike: 8000ms (threshold: 2000ms)"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "auth-service returning 500 for token validation"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "65% of authenticated requests failing, circuit breaker engaged for auth-service"},
                {"timestamp": _ts(2, 30), "level": "WARN", "message": "Product and search routes still functional (no auth required for browsing)"},
            ],
        },
        "service_configs": {
            "cache": {**_BASE_CONFIG, "version": "Redis 7.2", "tls_enabled": True, "tls_cert_path": "/etc/redis/tls/redis.crt", "tls_key_path": "/etc/redis/tls/redis.key", "tls_cert_expiry": "2026-04-03T23:59:59Z", "mutual_tls": True},
            "auth-service": {**_BASE_CONFIG, "cache_backend": "redis://cache.internal:6379", "session_ttl_seconds": 3600, "db_fallback_enabled": True},
            "api-gateway": {**_BASE_CONFIG, "circuit_breaker_threshold": 10, "auth_required_routes": ["/api/users/*", "/api/payments/*", "/api/settings/*"]},
        },
        "traces": [
            {
                "trace_id": "trace-201",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 8500, "status": "error", "timestamp": _ts(1, 30)},
                    {"service": "auth-service", "operation": "validate_session", "duration_ms": 8000, "status": "error", "error": "cache TLS connection expired, DB fallback timeout", "timestamp": _ts(1, 30)},
                    {"service": "cache", "operation": "get_session", "duration_ms": 0, "status": "error", "error": "TLS handshake failed: certificate expired", "timestamp": _ts(1, 30)},
                ],
            },
            {
                "trace_id": "trace-202",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 50, "status": "ok", "timestamp": _ts(2, 0)},
                    {"service": "product-service", "operation": "list_products", "duration_ms": 30, "status": "ok", "timestamp": _ts(2, 0)},
                ],
            },
            {
                "trace_id": "trace-203",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 8200, "status": "error", "timestamp": _ts(2, 30)},
                    {"service": "auth-service", "operation": "validate_session", "duration_ms": 8000, "status": "error", "error": "Redis TLS cert expired, session lookup failed", "timestamp": _ts(2, 30)},
                    {"service": "cache", "operation": "connect", "duration_ms": 0, "status": "error", "error": "SSL_ERROR_EXPIRED_CERT_ALERT", "timestamp": _ts(2, 30)},
                ],
            },
        ],
        "alerts": [
            {"timestamp": _ts(0, 10), "service": "cache", "severity": "warning", "message": "TLS certificate expiring in <24 hours"},
            {"timestamp": _ts(0, 30), "service": "cache", "severity": "critical", "message": "TLS certificate EXPIRED"},
            {"timestamp": _ts(1, 0), "service": "auth-service", "severity": "critical", "message": "Cache connection failures, error rate rising"},
            {"timestamp": _ts(1, 30), "service": "api-gateway", "severity": "warning", "message": "Auth latency above threshold (8000ms)"},
            {"timestamp": _ts(2, 0), "service": "api-gateway", "severity": "critical", "message": "5xx error rate above 60%"},
        ],
    },

    # ── Scenario 4: Search Index Corruption ──
    {
        "id": "search_index_corruption",
        "description": "Product search is returning empty results or irrelevant items. The product catalog team reports that product data looks correct in the database. Investigate the outage across all services.",
        "root_cause_service": "search-service",
        "root_cause_description_keywords": ["index", "corrupt", "Elasticsearch", "reindex", "disk", "partial write", "search"],
        "failure_chain": ["search-service", "product-service", "api-gateway"],
        "remediation_steps": [
            "Delete corrupted search index and trigger full reindex from product-db",
            "Increase disk allocation on search-service nodes from 50GB to 200GB",
            "Monitor product-service fallback to direct DB queries during reindex",
            "Add pre-flight disk space check before reindex jobs",
        ],
        "remediation_keywords": [
            ["delete", "corrupted", "reindex", "product-db"],
            ["increase", "disk", "search-service", "200GB"],
            ["monitor", "product-service", "fallback", "DB"],
            ["pre-flight", "disk", "check", "reindex"],
        ],
        "service_statuses": {
            "api-gateway": "degraded",
            "auth-service": "healthy",
            "user-service": "healthy",
            "user-db": "healthy",
            "product-service": "degraded",
            "product-db": "healthy",
            "search-service": "unhealthy",
            "payment-service": "healthy",
            "payment-gateway": "healthy",
            "queue": "healthy",
            "worker": "healthy",
            "notification-service": "healthy",
            "cache": "healthy",
            "email-provider": "healthy",
        },
        "service_metrics": {
            "search-service": {"cpu": 90, "memory": 85, "latency_ms": 0, "error_rate": 1.0, "throughput": 0, "connections": 0},
            "product-service": {"cpu": 65, "memory": 60, "latency_ms": 3500, "error_rate": 0.40, "throughput": 50, "connections": 30},
            "api-gateway": {"cpu": 45, "memory": 42, "latency_ms": 4000, "error_rate": 0.30, "throughput": 120, "connections": 180},
        },
        "service_logs": {
            "search-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Elasticsearch 8.11 cluster healthy, index 'products_v2' serving queries"},
                {"timestamp": _ts(0, 30), "level": "INFO", "message": "Reindex job started for product index 'products_v2' (1.2M documents)"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "Disk usage at 92% (46GB/50GB) during reindex — index write consuming remaining space"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "ENOSPC: disk full at 50GB/50GB during index write, reindex aborted at 60% completion"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Elasticsearch index 'products_v2' is in RED state: 3 of 5 primary shards UNASSIGNED due to partial write"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "All search queries returning 0 results: index corrupted, shard allocation failed"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "Health check FAILED: index 'products_v2' unrecoverable without manual intervention"},
            ],
            "product-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Product queries routed to search-service, avg latency 50ms"},
                {"timestamp": _ts(2, 0), "level": "WARN", "message": "search-service returning 0 results for all queries, engaging DB fallback"},
                {"timestamp": _ts(2, 30), "level": "WARN", "message": "Fallback: querying product-db directly, response time 3500ms (normal via search: 50ms)"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "DB fallback under heavy load: 40% of queries timing out at 5000ms threshold"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Routing search requests to product-service"},
                {"timestamp": _ts(2, 0), "level": "WARN", "message": "Product search latency spike: 3500ms (threshold: 1000ms)"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "Search endpoint degraded: 30% error rate, latency at 4000ms"},
                {"timestamp": _ts(3, 0), "level": "WARN", "message": "User-facing search returning partial or empty results"},
            ],
        },
        "service_configs": {
            "search-service": {**_BASE_CONFIG, "version": "Elasticsearch 8.11", "disk_size": "50GB", "index_name": "products_v2", "shards": 5, "replicas": 1},
            "product-service": {**_BASE_CONFIG, "search_fallback_enabled": True, "db_query_timeout_ms": 5000},
            "api-gateway": {**_BASE_CONFIG},
        },
        "traces": [
            {
                "trace_id": "trace-301",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_search", "duration_ms": 4000, "status": "error", "timestamp": _ts(2, 30)},
                    {"service": "product-service", "operation": "search_products", "duration_ms": 3500, "status": "error", "error": "search-service returned 0 results, DB fallback timeout", "timestamp": _ts(2, 30)},
                    {"service": "search-service", "operation": "query_index", "duration_ms": 5, "status": "error", "error": "index 'products_v2' RED: shards unassigned, corrupt", "timestamp": _ts(2, 30)},
                ],
            },
            {
                "trace_id": "trace-302",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 60, "status": "ok", "timestamp": _ts(2, 45)},
                    {"service": "payment-service", "operation": "process_payment", "duration_ms": 30, "status": "ok", "timestamp": _ts(2, 45)},
                ],
            },
            {
                "trace_id": "trace-303",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_search", "duration_ms": 3800, "status": "ok", "timestamp": _ts(3, 0)},
                    {"service": "product-service", "operation": "search_products", "duration_ms": 3500, "status": "ok", "error": "search-service failed, fell back to product-db direct query", "timestamp": _ts(3, 0)},
                    {"service": "product-db", "operation": "query", "duration_ms": 3200, "status": "ok", "timestamp": _ts(3, 0)},
                ],
            },
        ],
        "alerts": [
            {"timestamp": _ts(1, 0), "service": "search-service", "severity": "warning", "message": "Disk usage above 90% during reindex"},
            {"timestamp": _ts(1, 30), "service": "search-service", "severity": "critical", "message": "Reindex aborted: disk full"},
            {"timestamp": _ts(2, 0), "service": "search-service", "severity": "critical", "message": "Index 'products_v2' RED: shards unassigned"},
            {"timestamp": _ts(2, 30), "service": "product-service", "severity": "warning", "message": "Search fallback active, latency above threshold"},
            {"timestamp": _ts(3, 0), "service": "api-gateway", "severity": "warning", "message": "Search endpoint error rate above 25%"},
        ],
    },

    # ── Scenario 5: Notification Email Storm ──
    {
        "id": "notification_email_storm",
        "description": "The email delivery system is overwhelmed and users are complaining about delayed or missing notifications. Some users report receiving duplicate emails. Investigate the outage across all services.",
        "root_cause_service": "worker",
        "root_cause_description_keywords": ["retry", "loop", "infinite", "requeue", "exponential", "worker", "misconfigured"],
        "failure_chain": ["worker", "queue", "notification-service", "email-provider"],
        "remediation_steps": [
            "Stop the worker and drain the poisoned messages from the queue",
            "Fix the retry logic in worker to use max_retries=3 with exponential backoff",
            "Restart notification-service and clear the email rate limit block with email-provider",
            "Add dead letter queue handling and circuit breaker for notification retries",
        ],
        "remediation_keywords": [
            ["stop", "worker", "drain", "queue", "messages"],
            ["fix", "retry", "max_retries", "backoff", "worker"],
            ["restart", "notification-service", "rate limit", "email-provider"],
            ["dead letter", "circuit breaker", "notification"],
        ],
        "service_statuses": {
            "api-gateway": "healthy",
            "auth-service": "healthy",
            "user-service": "healthy",
            "user-db": "healthy",
            "product-service": "healthy",
            "product-db": "healthy",
            "search-service": "healthy",
            "payment-service": "healthy",
            "payment-gateway": "healthy",
            "queue": "degraded",
            "worker": "unhealthy",
            "notification-service": "unhealthy",
            "cache": "healthy",
            "email-provider": "degraded",
        },
        "service_metrics": {
            "worker": {"cpu": 95, "memory": 88, "latency_ms": 100, "error_rate": 0.95, "throughput": 2000, "connections": 50},
            "queue": {"cpu": 70, "memory": 75, "latency_ms": 500, "error_rate": 0.0, "throughput": 5000, "connections": 100},
            "notification-service": {"cpu": 92, "memory": 80, "latency_ms": 15000, "error_rate": 0.75, "throughput": 10, "connections": 5},
            "email-provider": {"cpu": 20, "memory": 30, "latency_ms": 30000, "error_rate": 0.90, "throughput": 1, "connections": 2},
        },
        "service_logs": {
            "worker": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Worker started, consuming from queue topic 'notifications'"},
                {"timestamp": _ts(0, 30), "level": "WARN", "message": "Retry policy misconfigured: max_retries=0 (unlimited), backoff_ms=0 — requeuing failed events immediately"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "message": "Event evt-5001 failed: notification-service returned 429. Requeuing immediately (retry #12)"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "Requeued notification event evt-5001 for 47th time in 3 minutes"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Queue depth exploding: 150000 messages (was 200 five minutes ago), 98% are retry duplicates"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "Worker CPU at 95%: all time spent requeuing failed events in tight loop"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "Infinite retry storm: 0 events successfully processed, all immediately fail and requeue"},
            ],
            "queue": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Queue depth: 200 messages (normal)"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "Queue depth growing rapidly: 15000 messages, consumer producing more messages than consuming"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Queue depth critical: 150000 messages, consumer lag 149800, memory pressure at 75%"},
                {"timestamp": _ts(3, 0), "level": "ERROR", "message": "Queue depth: 250000 messages, approaching max capacity. 98% are duplicate retry events from worker"},
            ],
            "notification-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Notification service running, connected to email-provider"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "Email send rate: 5000 req/min (limit: 100 req/min), email-provider returning 429"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "Rate limited by email-provider: 429 Too Many Requests (limit: 100/min, attempted: 5000/min)"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Email delivery halted: 0 emails delivered in last 5 minutes, 12000 pending in local buffer"},
                {"timestamp": _ts(2, 30), "level": "ERROR", "message": "email-provider account blocked for 60 minutes due to rate limit violation"},
            ],
            "email-provider": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Email provider API healthy, rate limit: 100 requests/min per account"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "Rate limit exceeded for account devops-app: 5000 req/min (limit: 100)"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Account devops-app BLOCKED: rate limit exceeded by 50x, all requests rejected for 60 minutes"},
            ],
        },
        "service_configs": {
            "worker": {**_BASE_CONFIG, "max_retries": 0, "retry_backoff_ms": 0, "consume_topic": "notifications"},
            "queue": {**_BASE_CONFIG, "version": "RabbitMQ 3.12", "max_queue_depth": 500000, "dead_letter_enabled": False},
            "notification-service": {**_BASE_CONFIG, "email_rate_limit": 100, "local_buffer_max": 50000},
            "email-provider": {**_BASE_CONFIG, "version": "SendGrid API v3", "rate_limit_per_min": 100, "block_duration_min": 60},
        },
        "traces": [
            {
                "trace_id": "trace-401",
                "spans": [
                    {"service": "worker", "operation": "consume_event", "duration_ms": 50, "status": "error", "error": "notification-service returned 429, requeuing event", "timestamp": _ts(1, 30)},
                    {"service": "notification-service", "operation": "send_email", "duration_ms": 30, "status": "error", "error": "email-provider rate limit 429", "timestamp": _ts(1, 30)},
                    {"service": "email-provider", "operation": "deliver", "duration_ms": 1, "status": "error", "error": "account blocked: rate limit exceeded", "timestamp": _ts(1, 30)},
                ],
            },
            {
                "trace_id": "trace-402",
                "spans": [
                    {"service": "worker", "operation": "consume_event", "duration_ms": 5, "status": "error", "error": "event evt-5001 failed, requeuing (retry #47)", "timestamp": _ts(2, 0)},
                    {"service": "queue", "operation": "enqueue", "duration_ms": 2, "status": "ok", "timestamp": _ts(2, 0)},
                    {"service": "worker", "operation": "consume_event", "duration_ms": 5, "status": "error", "error": "event evt-5001 failed again, requeuing (retry #48)", "timestamp": _ts(2, 0)},
                ],
            },
            {
                "trace_id": "trace-403",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 50, "status": "ok", "timestamp": _ts(2, 30)},
                    {"service": "user-service", "operation": "get_user", "duration_ms": 20, "status": "ok", "timestamp": _ts(2, 30)},
                ],
            },
        ],
        "alerts": [
            {"timestamp": _ts(0, 30), "service": "worker", "severity": "warning", "message": "Retry policy: max_retries=0 (unlimited) detected"},
            {"timestamp": _ts(1, 0), "service": "notification-service", "severity": "critical", "message": "Email provider rate limit exceeded"},
            {"timestamp": _ts(1, 30), "service": "queue", "severity": "warning", "message": "Queue depth growing rapidly: 15000 messages"},
            {"timestamp": _ts(2, 0), "service": "worker", "severity": "critical", "message": "CPU at 95%, retry storm detected"},
            {"timestamp": _ts(2, 30), "service": "email-provider", "severity": "critical", "message": "Account blocked for 60 minutes"},
        ],
    },

    # ── Scenario 6: Cache Thundering Herd ──
    {
        "id": "cache_thundering_herd",
        "description": "After a brief cache restart for a planned maintenance patch, the auth-service and user-service are experiencing severe latency and the database is under extreme load. Investigate the outage across all services.",
        "root_cause_service": "cache",
        "root_cause_description_keywords": ["cold cache", "thundering herd", "cache miss", "restart", "stampede", "Redis", "empty"],
        "failure_chain": ["cache", "auth-service", "user-service", "user-db", "api-gateway"],
        "remediation_steps": [
            "Implement cache warming script to pre-populate hot keys before traffic resumes",
            "Add request coalescing in auth-service to prevent duplicate DB queries for the same key",
            "Increase user-db max_connections temporarily to handle the burst",
            "Configure cache with RDB/AOF persistence to survive restarts with data intact",
        ],
        "remediation_keywords": [
            ["cache warming", "pre-populate", "hot keys"],
            ["coalescing", "singleflight", "duplicate", "auth-service"],
            ["increase", "max_connections", "user-db", "burst"],
            ["persistence", "RDB", "AOF", "restart"],
        ],
        "service_statuses": {
            "api-gateway": "degraded",
            "auth-service": "unhealthy",
            "user-service": "unhealthy",
            "user-db": "unhealthy",
            "product-service": "healthy",
            "product-db": "healthy",
            "search-service": "healthy",
            "payment-service": "healthy",
            "payment-gateway": "healthy",
            "queue": "healthy",
            "worker": "healthy",
            "notification-service": "healthy",
            "cache": "degraded",
            "email-provider": "healthy",
        },
        "service_metrics": {
            "cache": {"cpu": 5, "memory": 10, "latency_ms": 1, "error_rate": 0.0, "throughput": 5000, "connections": 200},
            "auth-service": {"cpu": 85, "memory": 70, "latency_ms": 6000, "error_rate": 0.60, "throughput": 30, "connections": 50},
            "user-service": {"cpu": 80, "memory": 68, "latency_ms": 5500, "error_rate": 0.55, "throughput": 35, "connections": 50},
            "user-db": {"cpu": 98, "memory": 90, "latency_ms": 8000, "error_rate": 0.70, "throughput": 10, "connections": 500},
            "api-gateway": {"cpu": 50, "memory": 45, "latency_ms": 7000, "error_rate": 0.50, "throughput": 80, "connections": 200},
        },
        "service_logs": {
            "cache": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Redis restarted after maintenance patch (v7.2.1 -> v7.2.2), persistence disabled, all data evicted"},
                {"timestamp": _ts(0, 10), "level": "INFO", "message": "Redis accepting connections, 0 keys loaded — cold start"},
                {"timestamp": _ts(0, 30), "level": "WARN", "message": "Cache hit ratio: 0% (0 hits / 5000 requests in last 60s) — all requests are misses"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "Receiving 5000 req/s, 100% cache miss rate, all clients falling back to database"},
                {"timestamp": _ts(2, 0), "level": "INFO", "message": "Cache slowly warming: hit ratio 3% (150/5000), 150 keys populated from DB fallback responses"},
            ],
            "auth-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Session cache connected: redis://cache.internal:6379"},
                {"timestamp": _ts(0, 15), "level": "WARN", "message": "Cache MISS for session:user:* — falling back to user-db for ALL session lookups"},
                {"timestamp": _ts(0, 30), "level": "ERROR", "message": "DB query storm: 3000 concurrent session lookups to user-db (normal: 50 when cache warm)"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "message": "Session validation taking 6000ms (cache miss → DB fallback), auth requests timing out"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "60% of auth requests failing: cache empty, DB fallback overloaded by thundering herd"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "user-db returning 'too many connections' — all auth requests now failing"},
            ],
            "user-service": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Processing user requests, cache enabled for user profiles"},
                {"timestamp": _ts(0, 15), "level": "WARN", "message": "Cache miss rate 100%: all profile lookups routing to user-db"},
                {"timestamp": _ts(0, 30), "level": "ERROR", "message": "user-db connection pool saturated: 50/50 connections in use, 200 requests queued"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "message": "Request timeout: GET /users/123 took 5500ms (DB overloaded by concurrent cache-miss queries)"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "55% of user requests failing: thundering herd from cold cache overwhelming user-db"},
            ],
            "user-db": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "PostgreSQL 15.4 running, max_connections=500"},
                {"timestamp": _ts(0, 15), "level": "WARN", "message": "Connection spike: 200 new connections in 10 seconds (normal: 20/min)"},
                {"timestamp": _ts(0, 30), "level": "WARN", "message": "Active connections: 400/500, query latency p99: 3000ms (normal: 50ms)"},
                {"timestamp": _ts(1, 0), "level": "ERROR", "message": "FATAL: too many clients already (active: 500, max: 500) — thundering herd from cold cache"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "Query latency p99: 8000ms, 200 queries queued, connection pool exhausted"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Rejecting all new connections: max_connections=500 reached, pg_stat_activity shows 500 active, 350 idle in transaction"},
            ],
            "api-gateway": [
                {"timestamp": _ts(0, 0), "level": "INFO", "message": "Routing requests normally"},
                {"timestamp": _ts(0, 30), "level": "WARN", "message": "auth-service latency spike: 6000ms (threshold: 2000ms)"},
                {"timestamp": _ts(1, 0), "level": "WARN", "message": "user-service latency spike: 5500ms (threshold: 2000ms)"},
                {"timestamp": _ts(1, 30), "level": "ERROR", "message": "Upstream auth-service and user-service both returning 5xx, error rate 50%"},
                {"timestamp": _ts(2, 0), "level": "ERROR", "message": "Circuit breaker OPEN for auth-service and user-service"},
            ],
        },
        "service_configs": {
            "cache": {**_BASE_CONFIG, "version": "Redis 7.2.2", "persistence": "disabled", "max_memory": "2GB", "restarted_at": _ts(0, 0)},
            "auth-service": {**_BASE_CONFIG, "cache_ttl_seconds": 3600, "db_fallback_enabled": True},
            "user-service": {**_BASE_CONFIG, "cache_enabled": True, "db_connection_pool_size": 50},
            "user-db": {**_BASE_CONFIG, "version": "PostgreSQL 15.4", "max_connections": 500, "shared_buffers": "512MB"},
            "api-gateway": {**_BASE_CONFIG, "circuit_breaker_threshold": 10},
        },
        "traces": [
            {
                "trace_id": "trace-501",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 6500, "status": "error", "timestamp": _ts(1, 0)},
                    {"service": "auth-service", "operation": "validate_session", "duration_ms": 6000, "status": "error", "error": "cache miss, DB fallback timeout", "timestamp": _ts(1, 0)},
                    {"service": "cache", "operation": "get_session", "duration_ms": 1, "status": "ok", "error": "MISS: key not found (cold cache)", "timestamp": _ts(1, 0)},
                    {"service": "user-db", "operation": "query", "duration_ms": 5500, "status": "error", "error": "query timeout: too many concurrent connections", "timestamp": _ts(1, 0)},
                ],
            },
            {
                "trace_id": "trace-502",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 6000, "status": "error", "timestamp": _ts(1, 30)},
                    {"service": "user-service", "operation": "get_user", "duration_ms": 5500, "status": "error", "error": "cache miss, user-db max_connections reached", "timestamp": _ts(1, 30)},
                    {"service": "cache", "operation": "get_user", "duration_ms": 1, "status": "ok", "error": "MISS: key not found (cold cache)", "timestamp": _ts(1, 30)},
                    {"service": "user-db", "operation": "connect", "duration_ms": 0, "status": "error", "error": "FATAL: too many clients already (500/500)", "timestamp": _ts(1, 30)},
                ],
            },
            {
                "trace_id": "trace-503",
                "spans": [
                    {"service": "api-gateway", "operation": "handle_request", "duration_ms": 55, "status": "ok", "timestamp": _ts(1, 45)},
                    {"service": "product-service", "operation": "get_products", "duration_ms": 40, "status": "ok", "timestamp": _ts(1, 45)},
                    {"service": "product-db", "operation": "query", "duration_ms": 15, "status": "ok", "timestamp": _ts(1, 45)},
                ],
            },
        ],
        "alerts": [
            {"timestamp": _ts(0, 0), "service": "cache", "severity": "info", "message": "Redis restarted, 0 keys loaded (cold start)"},
            {"timestamp": _ts(0, 30), "service": "cache", "severity": "warning", "message": "Cache hit ratio 0% — all requests are misses"},
            {"timestamp": _ts(1, 0), "service": "user-db", "severity": "critical", "message": "Connection count at 500/500 — thundering herd detected"},
            {"timestamp": _ts(1, 0), "service": "auth-service", "severity": "critical", "message": "Error rate above 50%, DB fallback overloaded"},
            {"timestamp": _ts(1, 30), "service": "user-service", "severity": "critical", "message": "Error rate above 50%"},
            {"timestamp": _ts(2, 0), "service": "api-gateway", "severity": "critical", "message": "Circuit breaker open for auth-service and user-service"},
        ],
    },
]
