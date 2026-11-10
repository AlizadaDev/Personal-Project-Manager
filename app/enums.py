"""Fixed choice lists. The value is what users see and what is stored in the database."""

from enum import StrEnum


class ProjectStatus(StrEnum):
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"


class ProjectCategory(StrEnum):
    WEB_DEVELOPMENT = "Web Development"
    E_COMMERCE = "E-commerce"
    AI_AGENTS = "AI Agents"
    AUTOMATION = "Automation"
    CHATBOTS = "Chatbots"
    VOICE_AI = "Voice AI"
    AI_CONTENT = "AI Content"
    OTHER = "Other"


class TaskStatus(StrEnum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskPriority(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
