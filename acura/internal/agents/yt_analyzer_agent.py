from pydantic_ai import Agent
from internal.agents import decide_llm


class YoutubeAnalyzerAgent:
    def __init__(self):
        self.agent = Agent(model=decide_llm(
        ), system_prompt="""
        You are a Youtube video analyzer agent. Your task is to analyze Youtube videos and
        make sure to return true, in case you suspect that the video is a music video or it
        contains music. Otherwise you must return false. If unsure, return false.
        """, name="youtube_analyzer_agent", result_type=bool)

    async def check_is_music_video(self, title: str):
        flow = await self.agent.run(title)
        return flow.data
