# Alias package re-exporting Dev Agent knowledge graph
#
# This module provides a convenience alias for the knowledge_graph package
# located in agents/dev_agent/knowledge_graph/. It explicitly imports and
# re-exports submodules to ensure that imports like:
#   from knowledge_graph.knowledge_graph_manager import KnowledgeGraphManager
# work correctly regardless of PYTHONPATH order.
#
# Note: Wildcard imports (from X import *) only re-export names, not submodules.
# We must explicitly import submodules to make them available as attributes.

import sys
from agents.dev_agent import knowledge_graph as _kg

# Re-export all public names from the actual package
from agents.dev_agent.knowledge_graph import *  # noqa: F401,F403

# Explicitly import and register submodules so they're importable via this alias
from agents.dev_agent.knowledge_graph import knowledge_graph_manager  # noqa: F401
from agents.dev_agent.knowledge_graph import code_indexer  # noqa: F401
from agents.dev_agent.knowledge_graph import pattern_learner  # noqa: F401
from agents.dev_agent.knowledge_graph import embeddings_cache  # noqa: F401
from agents.dev_agent.knowledge_graph import bug_fix_pattern_learner  # noqa: F401
from agents.dev_agent.knowledge_graph import db_schema  # noqa: F401

# Register submodules in sys.modules so 'from knowledge_graph.X import Y' works
sys.modules['knowledge_graph.knowledge_graph_manager'] = knowledge_graph_manager
sys.modules['knowledge_graph.code_indexer'] = code_indexer
sys.modules['knowledge_graph.pattern_learner'] = pattern_learner
sys.modules['knowledge_graph.embeddings_cache'] = embeddings_cache
sys.modules['knowledge_graph.bug_fix_pattern_learner'] = bug_fix_pattern_learner
sys.modules['knowledge_graph.db_schema'] = db_schema
