import os
import re
from typing import Dict, List, Optional
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
from src.crew.tools.aws import SimplifiedAWSKnowledgeTool

load_dotenv()

@CrewBase
class AWSCrew():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        # Fix the API key assignment
        api_key = os.getenv('GEMINI_API_KEY')
        self.llm = LLM(model="gemini/gemini-2.0-flash-exp", api_key=api_key)
        self.searchtool = SerperDevTool()
        self.aws_tool = SimplifiedAWSKnowledgeTool()

    @agent
    def aws_query_agent(self) -> Agent:
        """
        Agent to handle AWS queries using the AWS Knowledge Tool
        """
        return Agent(
            config=self.agents_config['aws_query_agent'],
            tools=[self.aws_tool],
            llm=self.llm
        )

    @agent
    def search_agent(self) -> Agent:
        """
        Agent to handle web searches using Serper
        """
        return Agent(
            config=self.agents_config['search_agent'],
            tools=[self.searchtool],
            llm=self.llm
        )

    @agent
    def report_agent(self) -> Agent:
        """
        Agent to generate reports based on AWS queries and search results
        """
        return Agent(
            config=self.agents_config['report_agent'],
            llm=self.llm
        )

    @task
    def aws_query_task(self) -> Task:
        """
        Task to handle AWS queries
        """
        return Task(
            config=self.tasks_config['aws_query_task'],
            agent=self.aws_query_agent()
        )

    @task
    def search_task(self) -> Task:
        """
        Task to perform web searches
        """
        return Task(
            config=self.tasks_config['search_task'],
            agent=self.search_agent()
        )

    @task
    def report_task(self) -> Task:
        """
        Task to generate reports
        """
        return Task(
            config=self.tasks_config['report_task'],
            agent=self.report_agent()
        )
    
    @crew
    def crew(self) -> Crew:
        """
        Crew to manage AWS queries, web searches, and report generation
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
