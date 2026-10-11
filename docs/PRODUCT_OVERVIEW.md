# PRODUCT_OVERVIEW.md (sanitized public summary; the full PRD stays local-only)

The Services AI Platform is a multi-tenant foundation for building, evaluating,
deploying, and operating agentic AI workflows on AWS. Agents interact with enterprise
systems exclusively through governed API boundaries; retrieval combines vector and
graph stores; orchestration supports multiple planning patterns behind a plug-in
interface; and every prompt, model, retrieval config, and agent version passes
evaluation gates with auditability, quotas, and cost attribution built in.

Stack: Python/FastAPI backend, Angular frontend, PostgreSQL + pgvector, Neo4j,
containerized services, Terraform-managed AWS infrastructure.
