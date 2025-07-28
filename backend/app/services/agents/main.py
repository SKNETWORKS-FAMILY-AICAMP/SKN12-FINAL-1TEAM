# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import asyncio

from client_analysis_agent import graph, create_initial_state  

app = FastAPI()

from client_analysis_agent import preprocess_df
df = pd.read_excel("좋은제약_거래처정보.xlsx")
df = preprocess_df(df)

class ReportRequest(BaseModel):
    company_name: str
    start_month: Optional[str] = None
    end_month: Optional[str] = None


@app.post("/generate_report")
async def generate_report(request: ReportRequest):
    company_name = request.company_name
    start_month = request.start_month
    end_month = request.end_month

    if company_name not in df["거래처ID"].values:
        raise HTTPException(status_code=404, detail=f"{company_name} 거래처가 없습니다.")

    initial_state = create_initial_state(company_name, df, start_month, end_month)

    try:
        result = None
        final_state = initial_state.copy()
        async for res in graph.astream(initial_state):
            final_state.update(res)

        if "merged_report" not in final_state:
            raise HTTPException(status_code=500, detail="결과를 받지 못했습니다.")
        
        return {
            "company_name": company_name,
            "grade_result": final_state.get("grade_result"),
            "grade_report": final_state.get("grade_report"),
            "merged_report": final_state.get("merged_report")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
