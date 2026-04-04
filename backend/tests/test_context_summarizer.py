from app.core.nlp_pipeline.context_summarizer import context_summarizer

def test_project_summary_small_project():
    chapters = [
        {"title": "1", "summary": "Intro"},
        {"title": "2", "summary": "Meeting"}
    ]
    
    summary = context_summarizer.create_project_summary(chapters, window_size=3)
    
    assert "RECENT EVENTS" in summary
    assert "PREVIOUSLY" not in summary
    assert "Intro" in summary
    assert "Meeting" in summary

def test_project_summary_large_project():
    # 5 chapters, window=2
    chapters = [
        {"title": "1", "summary": "Ch1"},
        {"title": "2", "summary": "Ch2"},
        {"title": "3", "summary": "Ch3"},
        {"title": "4", "summary": "Ch4"},
        {"title": "5", "summary": "Ch5"}
    ]
    
    summary = context_summarizer.create_project_summary(chapters, window_size=2)
    
    assert "PREVIOUSLY (Chapters 1-3)" in summary
    assert "RECENT EVENTS" in summary
    
    # Check content
    assert "Ch1" in summary # In backstory
    assert "Ch5" in summary # In recent events

def test_project_summary_empty():
    assert context_summarizer.create_project_summary([]) == ""

def test_project_summary_missing_fields():
    chapters = [
        {"title": "1"}, # No summary
        {"title": "2", "summary": "Real summary"}
    ]
    summary = context_summarizer.create_project_summary(chapters, window_size=1)
    
    assert "Real summary" in summary
    assert "None" not in summary
