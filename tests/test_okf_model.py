from app.okf.okf_model import OKFKnowledgeItem


def test_okf_knowledge_item():
    item = OKFKnowledgeItem(
        title="Literature Review",
        type="Section",
        description="Review of existing literature.",
        source="Research Paper",
        start_page=2,
        end_page=3,
        content="This section reviews existing literature on learner autonomy.",
    )

    assert item.title == "Literature Review"
    assert item.type == "Section"
    assert item.start_page == 2
    assert item.end_page == 3
    assert item.source == "Research Paper"
    assert item.content != ""