import streamlit as st
import yfinance as yf
import pandas as pd

# ==========================================
# 1. ตั้งค่าหน้าจอ Dashboard
# ==========================================
st.set_page_config(page_title="Pro Global Asset Tracker", layout="wide", page_icon="📈")
st.title("🚀 Pro Global Asset Tracker & Buy Signals")
st.markdown("ระบบวิเคราะห์แนวโน้ม ค้นหาจุดเข้าซื้อ คำนวณความเสี่ยง และแสดงกราฟเทคนิคสำหรับหุ้นไทย หุ้นนอก และคริปโต")

# ==========================================
# 2. เมนูด้านข้าง (Sidebar) สำหรับตั้งค่าและอัปโหลด
# ==========================================
st.sidebar.header("⚙️ 1. การตั้งค่าสัญลักษณ์ (Ticker)")
ticker_mode = st.sidebar.radio(
    "รูปแบบสัญลักษณ์ในไฟล์ของคุณ:",
    options=[
        "ผสม (เช่น PTT.BK, AAPL, BTC-USD)", 
        "หุ้นไทยล้วน (เติม .BK ให้อัตโนมัติ)"
    ]
)

st.sidebar.header("📂 2. อัปโหลดไฟล์ Track set")
uploaded_file = st.sidebar.file_uploader("ลากไฟล์ Track set ของคุณมาวางที่นี่", type=["csv", "xlsx"])

# ใช้ลิสต์สำรองหากยังไม่อัปโหลดไฟล์
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
        st.sidebar.success(f"✅ โหลดสัญลักษณ์สำเร็จ {len(tickers)} รายการ")
    except Exception as e:
        st.sidebar.error("เกิดข้อผิดพลาดในการอ่านไฟล์ ใช้ค่าเริ่มต้นแทน")
        tickers = default_tickers
else:
    tickers = default_tickers

# ==========================================
# 3. ระบบประมวลผลสัญญาณซื้อขาย (Trading Logic)
# ==========================================
if st.sidebar.button("🔍 เริ่มสแกนหาสัญญาณเข้าซื้อ"):
    with st.spinner("กำลังดึงข้อมูลจากตลาดทั่วโลกและคำนวณตัวชี้วัด..."):
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
                
                # คำนวณเส้นค่าเฉลี่ย SMA 20 วัน
                hist['SMA20'] = hist['Close'].rolling(window=20).mean()
                curr_sma = float(hist['SMA20'].iloc[-1])
                prev_sma = float(hist['SMA20'].iloc[-2])
                
                # ฟีเจอร์ใหม่: คำนวณจุด Stop Loss เบื้องต้น (ต่ำกว่าราคาปัจจุบัน 3%) และแนวต้าน (High 20 วัน)
                stop_loss = current_price * 0.97
                resistance_20d = float(hist['High'].rolling(window=20).max().iloc[-1])
                
                asset_type = "คริปโต 🪙" if "-USD" in ticker else "หุ้นไทย 🇹🇭" if ".BK" in ticker else "หุ้นต่างประเทศ 🌎"
                
                # เงื่อนไขสัญญาณซื้อ (Breakout)
                signal = "⚪ รอดูสถานการณ์"
                if prev_price < prev_sma and current_price > curr_sma:
                    signal = "🟢 แนะนำซื้อ (Breakout)"
                elif current_price > curr_sma:
                    signal = "🟡 ถือรันเทรนด์ (Uptrend)"
                else:
                    signal = "🔴 แนวโน้มขาลง"
                
                results.append({
                    "สัญลักษณ์": ticker,
                    "ประเภท": asset_type,
                    "ราคาปัจจุบัน": current_price,
                    "เปลี่ยนแปลง (%)": pct_change,
                    "แนวรับ (SMA 20)": curr_sma,
                    "จุดตัดขาดทุน (Stop Loss)": stop_loss,
                    "แนวต้านระยะสั้น": resistance_20d,
                    "คำแนะนำประจำวัน": signal,
                    "History": hist[['Close', 'SMA20']] # เก็บข้อมูลไว้พลอตกราฟ
                })
            except Exception:
                pass
        
        # ==========================================
        # 4. ส่วนแสดงผล Dashboard
        # ==========================================
        df_results = pd.DataFrame(results)
        
        if not df_results.empty:
            st.markdown("---")
            
            # 4.1 ไฮไลต์ตัวที่น่าเข้าซื้อประจำวัน
            buy_df = df_results[df_results['คำแนะนำประจำวัน'] == "🟢 แนะนำซื้อ (Breakout)"]
            
            st.header("🔥 ตัวที่น่าเข้าซื้อประจำวัน (Daily Top Picks)")
            st.markdown("สินทรัพย์ที่มีสัญญาณเชิงบวก (ราคากำลังพุ่งทะลุเส้นค่าเฉลี่ย 20 วันในวันนี้ พร้อมระบบบริหารความเสี่ยง)")
            
            if not buy_df.empty:
                for _, row in buy_df.iterrows():
                    with st.container():
                        st.markdown(f"### 🎯 ซื้อ: **{row['สัญลักษณ์']}** ({row['ประเภท']})")
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("ราคาปัจจุบัน", f"{row['ราคาปัจจุบัน']:.2f}", f"{row['เปลี่ยนแปลง (%)']:.2f}%")
                        col2.metric("แนวรับ SMA20", f"{row['แนวรับ (SMA 20)]:.2f}")
                        col3.metric("จุดตัดขาดทุน (Stop Loss)", f"{row['จุดตัดขาดทุน (Stop Loss)]:.2f}")
                        col4.metric("แนวต้านถัดไป", f"{row['แนวต้านระยะสั้น']:.2f}")
                        
                        # ฟีเจอร์ใหม่: แสดงกราฟราคาของตัวที่น่าซื้อ
                        st.line_chart(row['History'])
                        st.markdown("---")
            else:
                st.info("ตลาดวันนี้ยังไม่มีสินทรัพย์ตัวไหนเกิดสัญญาณ 'Breakout' เพื่อเข้าซื้อครับ แนะนำให้รอดูสถานการณ์ไปก่อน")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 4.2 ตารางสรุปภาพรวมทั้งหมด พร้อมปุ่มดาวน์โหลด
            st.subheader("📊 ภาพรวมสินทรัพย์ทั้งหมด & เครื่องมือจัดการความเสี่ยง")
            
            # ตัดคอลัมน์ History ออกก่อนแสดงตาราง
            display_df = df_results.drop(columns=['History'])
            
            def color_signal(val):
                if "🟢" in val: return 'background-color: #e6f9ec; color: #006400; font-weight: bold;'
                elif "🟡" in val: return 'color: #b8860b;'
                elif "🔴" in val: return 'color: #8b0000;'
                return ''

            def color_pct(val):
                color = '#00C853' if val > 0 else '#D50000' if val < 0 else 'gray'
                return f'color: {color}; font-weight: bold;'
            
            st.dataframe(
                display_df.style
                .map(color_pct, subset=['เปลี่ยนแปลง (%)'])
                .map(color_signal, subset=['คำแนะนำประจำวัน'])
                .format({
                    "ราคาปัจจุบัน": "{:.2f}",
                    "เปลี่ยนแปลง (%)": "{:.2f}%",
                    "แนวรับ (SMA 20)": "{:.2f}",
                    "จุดตัดขาดทุน (Stop Loss)": "{:.2f}",
                    "แนวต้านระยะสั้น": "{:.2f}"
                }),
                use_container_width=True, height=500, hide_index=True
            )
            
            # ฟีเจอร์ใหม่: ปุ่มดาวน์โหลดไฟล์รายงานเป็น CSV
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 ดาวน์โหลดผลการวิเคราะห์ประจำวัน (CSV)",
                data=csv_data,
                file_name="daily_stock_analysis.csv",
                mime="text/csv"
            )
            
        else:
            st.error("ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบการเชื่อมต่ออินเทอร์เน็ตหรือรายชื่อสัญลักษณ์อีกครั้ง")

else:
    st.info("👈 กดปุ่ม **'🔍 เริ่มสแกนหาสัญญาณเข้าซื้อ'** ที่แถบด้านซ้ายมือเพื่อเริ่มต้นใช้งานได้ทันทีครับ (ระบบมีค่าเริ่มต้นตัวใหญ่ยอดฮิตให้เรียบร้อย)")
