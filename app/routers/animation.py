from fastapi import APIRouter, Query

router = APIRouter(tags=["animation"])

@router.get("/animation")
def get_animation(keyword: str = Query("栈")):
    if keyword == "栈":
        return {
            "type": "stack",
            "steps": [
                {"action": "push", "value": "A"},
                {"action": "push", "value": "B"},
                {"action": "pop"}
            ]
        }
    elif keyword == "队列":
        return {
            "type": "queue",
            "steps": [
                {"action": "enqueue", "value": "X"},
                {"action": "enqueue", "value": "Y"},
                {"action": "dequeue"}
            ]
        }
    else:
        return {
            "type": "basic",
            "steps": [
                {"action": "show", "value": keyword}
            ]
        }