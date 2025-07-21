from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from client_agent import graph
import asyncio

app = FastAPI()

class CompanyInput(BaseModel):
    name: str
    sales: int
    visits: int

@app.post("/run-report")
async def run_report(company: CompanyInput):
    try:
        first_state = {
            "target_company": {
                "name": company.name,
                "sales": company.sales,
                "visits": company.visits
            }
        }

        final_state = await graph.ainvoke(first_state)

        return {
            "등급": final_state.get("rating"),
            "등급 이유": final_state.get("grade_reason_report"),
            "영업 전략 보고서": final_state.get("sales_strategy_report"),
            "성장 요약 보고서": final_state.get("growth_summary_report"),
            "통합 보고서": final_state.get("merged_report")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))