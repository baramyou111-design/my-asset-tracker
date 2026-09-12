import streamlit as st
import yfinance as yf
import pandas as pd

# 1. ตั้งค่าหน้าจอ Dashboard
st.set_page_config(page_title="Pro Global Asset Tracker", layout="wide", page_icon="📈")
st.title("🚀 Pro Global Asset Tracker & Buy Signals")
st.markdown("ระบบวิเคราะห์แนวโน้ม ค้นหาจุดเข้าซื้อ คำนวณความเสี่ยง และแสดงกราฟเทคนิคสำหรับหุ้นไทย หุ้นนอก และคริปโต")

# 2. เมนูด้านข้าง (Sidebar) สำหรับตั้งค่าและอัปโหลด
st.sidebar.header("⚙️ 1. การตั้งค่าสัญลักษณ์")
ticker_mode = st.sidebar.radio(
    "รูปแบบสัญลักษณ์ในไฟล์:",
    options=[
        "ผสม (เช่น PTT.BK, AAPL, BTC-USD)", 
        "หุ้นไทยล้วน (เติม .BK ให้อัตโนมัติ)"
    ]
)

st.sidebar.header("📂 2. อัปโหลดไฟล์ Track set")
uploaded_file = st.sidebar.file_uploader("ลากไฟล์มาวางที่นี่", type=["csv", "xlsx"])

default_tickers = ["PTT.BK", "AOT.BK", "CPALL.BK", "AAPL", "TSLA", "NVDA", "BTC-USD", "ETH-USD"]

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_track = pd.read_csv(uploaded_file, header=None)
        else:
            df_track = pd.read_excel(uploaded_file, header=None)
        
        raw_tickers = df_track[0].dropna().astype(str).tolist()
        tickers = []
        for t in raw_tickers:
            t = t.strip().upper()
            if t and t not in ["ชื่อหุ้น", "TICKER", "SYMBOL", "สัญลักษณ์"]:
                if ticker_mode == "หุ้นไทยล้วน (เติม .BK ให้อัตโนมัติ)":
                    if not t.endswith('.BK'):
                        t += '.BK'
                tickers.append(t)
        st.sidebar.success(f"✅ โหลดสำเร็จ {len(tickers)} รายการ")
    except Exception:
        st.sidebar.error("เกิดข้อผิดพลาด ใช้ค่าเริ่มต้นแทน")
        tickers = default_tickers
else:
    tickers = default_tickers

# 3. ระบบประมวลผลสัญญาณ
if st.sidebar.button("🔍 เริ่มสแกนหาสัญญาณเข้าซื้อ"):
    with st.spinner("กำลังดึงข้อมูลและคำนวณตัวชี้วัด..."):
        results = []
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                if hist.empty or len(hist) < 20:
                    continue
                    
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2])
                pct_change = ((current_price - prev_price) / prev_price) * 100
                
                hist['SMA20'] = hist['Close'].rolling(window=20).mean()
                curr_sma = float(hist['SMA20'].iloc[-1])
                prev_sma = float(hist['SMA20'].iloc[-2])
                
                stop_loss = current_price * 0.97
                resistance_20d = float(hist['High'].rolling(window=20).max().iloc[-1])
                
                asset_type = "คริปโต" if "-USD" in ticker else "หุ้นไทย" if ".BK" in ticker else "หุ้นต่างประเทศ"
                
                signal = "⚪ รอดูสถานการณ์"
                if prev_price < prev_sma and current_price > curr_sma:
                    signal = "🟢 แนะนำซื้อ (Breakout)"
                elif current_price > curr_sma:
                    signal = "🟡 ถือรันเทรนด์"
                else:
                    signal = "🔴 แนวโน้มขาลง"
                
                results.append({
                    "สัญลักษณ์": ticker,
                    "ประเภท": asset_type,
                    "ราคาปัจจุบัน": current_price,
                    "เปลี่ยนแปลง (%)": pct_change,
                    "แนวรับ SMA20": curr_sma,
                    "Stop Loss": stop_loss,
                    "แนวต้าน": resistance_20d,
                    "คำแนะนำ": signal,
                    "History": hist[['Close', 'SMA20']]
                })
            except Exception:
                pass
        
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            st.markdown("---")
            buy_df = df_results[df_results['คำแนะนำ'] == "🟢 แนะนำซื้อ (Breakout)"]
            
            st.header("🔥 ตัวที่น่าเข้าซื้อประจำวัน")
            if not buy_df.empty:
                for _, row in buy_df.iterrows():
                    st.markdown(f"### 🎯 ซื้อ: {row['สัญลักษณ์']} ({row['ประเภท']})")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("ราคาปัจจุบัน", f"{row['ราคาปัจจุบัน']:.2f}", f"{row['เปลี่ยนแปลง (%)']:.2f}%")
                    c2.metric("แนวรับ SMA20", f"{row['แนวรับ SMA20']:.2f}")
                    c3.metric("Stop Loss", f"{row['Stop Loss']:.2f}")
                    c4.metric("แนวต้าน", f"{row['แนวต้าน']:.2f}")
                    st.line_chart(row['History'])
                    st.markdown("---")
            else:
                st.info("วันนี้ยังไม่มีสินทรัพย์เกิดสัญญาณ Breakout รอดูสถานการณ์ก่อนครับ")
            
            st.subheader("📊 ภาพรวมทั้งหมด")
            display_df = df_results.drop(columns=['History'])
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 ดาวน์โหลดรายงาน CSV", data=csv_data, file_name="stock_report.csv", mime="text/csv")
        else:
            st.error("ไม่สามารถดึงข้อมูลได้ ลองตรวจสอบสัญลักษณ์ใหม่อีกครั้งครับ")
else:
    st.info("👈 กดปุ่ม **'🔍 เริ่มสแกนหาสัญญาณเข้าซื้อ'** ที่แถบเมนูด้านซ้ายมือเพื่อเริ่มใช้งานได้เลยครับ")
