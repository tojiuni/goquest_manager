from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date


class SubIssue(BaseModel):
    name: str
    priority: Optional[str] = "none"


class Issue(BaseModel):
    name: str
    priority: Optional[str] = "none"
    cycle: Optional[str] = None
    module: Optional[str] = None
    sub_issues: Optional[List[SubIssue]] = []


class Cycle(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class Module(BaseModel):
    name: str


class Project(BaseModel):
    name: str
    cycles: Optional[List[Cycle]] = []
    modules: Optional[List[Module]] = []
    issues: Optional[List[Issue]] = []


class BatchTemplate(BaseModel):
    batch_name: str
    workspace_slug: str
    projects: List[Project]