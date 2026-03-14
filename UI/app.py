import streamlit as st
import pandas as pd
import chess.pgn
import chess.svg
import base64
import io
import os

from engine_service import EngineClient
from analyzer import GameAnalyzerFacade

st.set_page_config(page_title="Advanced Chess Analytics", layout="wide")

def render_svg_board(fen: str, size: int = 400):
    """Renders a chess board as an SVG string for Streamlit."""
    board = chess.Board(fen)
    svg = chess.svg.board(board, size=size)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f'<img src="data:image/svg+xml;base64,{b64}" style="border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>'

st.title("Deep Positional Chess Analyzer")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("Engine Configuration")
    # Automatically use the container's Stockfish if in Docker, otherwise fallback
    default_sf = os.environ.get("STOCKFISH_PATH", "/usr/bin/stockfish")
    sf_path = st.text_input("Stockfish Path", value=default_sf)
    depth = st.slider("Analysis Depth", min_value=10, max_value=24, value=16)
    
    st.header("Input Game")
    input_method = st.radio("Choose Input Method:", ["Upload PGN File", "Paste PGN Text"])
    
    pgn_string = ""
    if input_method == "Upload PGN File":
        uploaded_file = st.file_uploader("Upload a PGN file", type=["pgn"])
        if uploaded_file:
            pgn_string = uploaded_file.getvalue().decode("utf-8")
    else:
        pgn_string = st.text_area("Paste your raw PGN here:", height=200)

# --- MAIN LOGIC ---
# Change the trigger condition to check if pgn_string has content
if pgn_string and st.sidebar.button("Analyze Game"):
    pgn_io = io.StringIO(pgn_string)
    game = chess.pgn.read_game(pgn_io)
    
    if game:
        with st.spinner("This may take a few minutes..."):
            engine = EngineClient(sf_path, depth)
            analyzer = GameAnalyzerFacade(engine)
            report = analyzer.analyze_game(game)
            engine.close()
            
        st.success("Analysis Complete!")
        
        # --- TAB LAYOUT ---
        tab_overview, tab_charts, tab_critical, tab_log = st.tabs([
            "Overview & Stats", "Positional Dynamics", "Critical Positions", "Annotated Log"
        ])
        
        # TAB 1: OVERVIEW
        with tab_overview:
            st.header(f"{report.white} vs {report.black}")
            st.subheader(f"Result: {report.result}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### ⬜ White: {report.white}")
                st.write(f"**Accuracy:** {report.white_stats.accuracy:.1f}%")
                st.write(f"**Avg CP Loss:** {report.white_stats.avg_centipawn_loss:.1f}")
                st.write(f"**Best/Good:** {report.white_stats.classifications['best']} / {report.white_stats.classifications['good']}")
                st.write(f"**Mistakes/Blunders:** {report.white_stats.classifications['mistake']} / {report.white_stats.classifications['blunder']}")
                
            with col2:
                st.markdown(f"### ⬛ Black: {report.black}")
                st.write(f"**Accuracy:** {report.black_stats.accuracy:.1f}%")
                st.write(f"**Avg CP Loss:** {report.black_stats.avg_centipawn_loss:.1f}")
                st.write(f"**Best/Good:** {report.black_stats.classifications['best']} / {report.black_stats.classifications['good']}")
                st.write(f"**Mistakes/Blunders:** {report.black_stats.classifications['mistake']} / {report.black_stats.classifications['blunder']}")

        # TAB 2: CHARTS
        with tab_charts:
            df = pd.DataFrame([{
                'Ply': m.ply, 'Eval': m.eval_cp / 100.0,
                'Space (W)': m.positional_metrics.space_w, 'Space (B)': m.positional_metrics.space_b,
                'Mobility (W)': m.positional_metrics.mobility_w, 'Mobility (B)': m.positional_metrics.mobility_b,
                'King Safety (W)': m.positional_metrics.king_safety_w, 'King Safety (B)': m.positional_metrics.king_safety_b,
                'Threats (W)': m.positional_metrics.threats_w, 'Threats (B)': m.positional_metrics.threats_b,
            } for m in report.moves]).set_index('Ply')

            st.subheader("Position Evaluation Over Time")
            st.line_chart(df['Eval'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Space Control")
                st.line_chart(df[['Space (W)', 'Space (B)']])
                st.subheader("King Safety")
                st.line_chart(df[['King Safety (W)', 'King Safety (B)']])
            with col2:
                st.subheader("Piece Mobility")
                st.line_chart(df[['Mobility (W)', 'Mobility (B)']])
                st.subheader("Threats")
                st.line_chart(df[['Threats (W)', 'Threats (B)']])

        # TAB 3: CRITICAL POSITIONS
        with tab_critical:
            st.header("Critical Moments")
            st.write("Positions representing the biggest evaluation swings in the game.")
            
            for i, cp in enumerate(report.critical_positions[:8]): # Show top 8 swings
                move_num = (cp.ply + 1) // 2
                color_indicator = "White" if cp.ply % 2 != 0 else "Black"
                
                st.markdown("---")
                st.markdown(f"### Position {i+1}: After {move_num}. {'...' if color_indicator == 'Black' else ''}{cp.move_san}")
                st.markdown(f"*{cp.reason}*")
                st.markdown(f"**Evaluation:** {cp.eval_score / 100.0:+.2f}")
                
                board_col, metrics_col = st.columns([1, 1])
                
                with board_col:
                    st.markdown(render_svg_board(cp.fen), unsafe_allow_html=True)
                    
                with metrics_col:
                    # Construct the metrics table
                    metrics_data = {
                        "Metric": ["Space", "Mobility", "King Safety", "Threats"],
                        "White": [f"{cp.metrics.space_w:.2f}", f"{cp.metrics.mobility_w:.2f}", f"{cp.metrics.king_safety_w:.2f}", f"{cp.metrics.threats_w:.2f}"],
                        "Black": [f"{cp.metrics.space_b:.2f}", f"{cp.metrics.mobility_b:.2f}", f"{cp.metrics.king_safety_b:.2f}", f"{cp.metrics.threats_b:.2f}"]
                    }
                    st.table(pd.DataFrame(metrics_data).set_index("Metric"))
                    
                    st.markdown(f"**Instead of {cp.move_san}:** {', '.join(cp.instead_of)}")
                    st.markdown(f"**Best continuation:** {' '.join(cp.best_continuation)}")

        # TAB 4: ANNOTATED LOG
        with tab_log:
            st.header("Annotated Game Log")
            log_text = ""
            for m in report.moves:
                move_num = (m.ply + 1) // 2
                prefix = f"**{move_num}.** " if m.is_white else f"**{move_num}...** "
                
                annotation = ""
                if m.classification in ["blunder", "mistake"]:
                    annotation = f" ❓ *(Loses {int(m.eval_loss)}cp. Consider: {m.best_move_san})*"
                elif m.classification == "inaccuracy":
                    annotation = f" ⁈"
                elif m.classification == "best" and m.eval_loss == 0:
                    annotation = f" ⭐"
                    
                log_text += f"{prefix}{m.san}{annotation} \n\n"
            
            st.markdown(log_text)