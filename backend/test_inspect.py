
import pytest
import asyncio
from app.tasks.nlp_tasks import translate_chapter_task

def test_inspect():
    print('run type:', type(translate_chapter_task.run))
    print('wrapped:', hasattr(translate_chapter_task, '__wrapped__'))

