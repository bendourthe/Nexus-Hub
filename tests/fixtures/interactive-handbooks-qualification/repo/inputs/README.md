# Aster Fieldworks Queue

A synthetic field-observation queue. Configuration controls retry attempts, admission capacity and timeout. Incoming observations enter the queue, an analyst reviews them, and approved records are archived. No reliability measurement is available. Current code/config is authoritative; the generated handbook predates the retry-limit change. Keep the native build.py entry point and the existing handbook URL/anchors when refreshing it.
