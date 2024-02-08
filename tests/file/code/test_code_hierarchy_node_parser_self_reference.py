"""Test CodeHierarchyNodeParser reading itself."""
from typing import Sequence
from llama_index import SimpleDirectoryReader
from pytest import fixture
from llama_hub.file.code.code_hierarchy import CodeHierarchyNodeParser
from llama_index.text_splitter import CodeSplitter
from pathlib import Path
from llama_index.schema import BaseNode, NodeRelationship

from IPython.display import Markdown, display

from llama_hub.file.code.index import CodeHierarchyKeywordQueryEngine
def print_python(python_text: str) -> None:
    """This function prints python text in ipynb nicely formatted."""
    display(Markdown("```python\n"+python_text+"```"))

@fixture
def code_hierarchy_nodes():
    reader = SimpleDirectoryReader(
        input_files=[Path("../../../llama_hub/file/code/code_hierarchy.py")],
        file_metadata=lambda x: {"filepath": x},
    )
    nodes = reader.load_data()
    split_nodes = CodeHierarchyNodeParser(
        language="python",
        # You can further parameterize the CodeSplitter to split the code
        # into "chunks" that match your context window size using
        # chunck_lines and max_chars parameters, here we just use the defaults
        code_splitter=CodeSplitter(language="python", max_chars=1000, chunk_lines=10),
    ).get_nodes_from_documents(nodes)

    return split_nodes

def test_code_splitter_NEXT_relationship_indention(code_hierarchy_nodes: Sequence[BaseNode]) -> None:
    """When using jupyter I found that the final brevity comment was indented when it shouldnt be"""
    print_python(code_hierarchy_nodes[0].text)
    assert not code_hierarchy_nodes[0].split("\n")[-1].starts_with(" "), "The last line should not be indented"

def test_query_by_module_name(code_hierarchy_nodes: Sequence[BaseNode]) -> None:
    """Test querying the index by filename."""
    index = CodeHierarchyKeywordQueryEngine(code_hierarchy_nodes)
    query = "code_hierarchy"
    results = index.query(query)
    assert len(results) >= 1

def test_query_by_name(code_hierarchy_nodes: Sequence[BaseNode]) -> None:
    """Test querying the index by signature."""
    index = CodeHierarchyKeywordQueryEngine(code_hierarchy_nodes)
    query = "CodeHierarchyNodeParser"
    results = index.query(query)
    assert len(results) >= 1

def test_parent_but_no_previous(code_hierarchy_nodes: Sequence[BaseNode]) -> None:
    """Test that the root of a query has no previous nodes."""
    query = "CodeHierarchyNodeParser"
    for node in code_hierarchy_nodes:
        if query == node.metadata.get("inclusive_scopes", [{"name": ""}])[-1]["name"]:
            assert NodeRelationship.PREVIOUS not in node.relationships, "The root of a query should have no previous nodes"