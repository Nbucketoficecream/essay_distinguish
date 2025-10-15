#coding:utf-8
import re
import gradio as gr
import essay_classify as ec
def gradio_process(names: str):
    web, paper, notfound = [], [], []
    titles = [n.strip() for n in re.split(r"[,，\n]+", names) if n.strip()]

    for title in titles:
        res = ec.classify(title) or ["", "", ""]
        # 期望 res = [web_status, paper_status, url]
        web_status  = res[0] if len(res) > 0 else ""
        paper_status= res[1] if len(res) > 1 else ""
        url         = res[2] if len(res) > 2 else ""

        # 驗證碼
        if web_status in ("驗證碼審查", "驗證碼審查機制"):
            notfound.append(f"{title}（驗證碼審查）")
            continue

        if web_status == "電子全文":
            web.append(f"{title} → {url or '(無連結)'}")
        if paper_status == "紙本全文":
            paper.append(f"{title} → {url or '(無連結)'}")

        # 兩者都沒有就歸到未找到/無全文
        if not web_status and not paper_status:
            notfound.append(title)

    return (
        "\n".join(web) if web else "沒有電子全文資料",
        "\n".join(paper) if paper else "沒有紙本全文資料",
        "\n".join(notfound) if notfound else "全部都有找到！"
    )



demo = gr.Interface(
    fn=gradio_process,
    inputs=gr.Textbox(label="請輸入論文名稱（以逗號分隔）"),
    outputs=[
        gr.Textbox(label="電子全文"),   # 對應 return 第 1 個
        gr.Textbox(label="紙本全文"),   # 對應 return 第 2 個
        gr.Textbox(label="未找到")      # 對應 return 第 3 個
    ],
    title="論文分類系統",
    flagging_mode="never" 
)

demo.launch(server_name="127.0.0.1", server_port=5050,debug= True)







