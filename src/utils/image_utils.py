from PIL import Image, ImageDraw, ImageFont
import io
import os

def embed_text_on_image(image_bytes: bytes, text_to_embed: str) -> bytes:
    """
    画像にテキストを埋め込む。

    Args:
        image_bytes (bytes): 元の画像のバイトデータ。
        text_to_embed (str): 埋め込むテキスト。

    Returns:
        bytes: テキストが埋め込まれた画像のバイトデータ (PNG形式)。
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(image)

        # テキストを複数行に分割（ここでは単純な改行文字での分割を想定）
        # より高度な自動改行処理が必要な場合は、textwrapモジュールなどを検討
        lines = text_to_embed.split('\n')
        
        # フォントの探索と設定
        font_path = None
        # 一般的な日本語フォントのパス (環境に合わせて調整が必要)
        font_paths = [
            "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",  # macOS (Hiragino Sans W3)
            "C:/Windows/Fonts/YuGothM.ttc",              # Windows (游ゴシック Medium)
            "C:/Windows/Fonts/meiryo.ttc",               # Windows (メイリオ)
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", # Linux (Noto Sans CJK JP Regular)
            "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf" # Linux (Takao P Gothic)
        ]
        
        for fp in font_paths:
            if os.path.exists(fp):
                font_path = fp
                break
        
        # 画像の幅に基づいてフォントサイズを決定 (例)
        # より洗練された方法として、テキストの長さに応じた調整も考えられる
        font_size = max(15, int(image.width / 25)) # 最低フォントサイズを15とする
        
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            # フォントが見つからない場合はPillowのデフォルトフォントを使用
            # (日本語は表示できない可能性が高い)
            print("Warning: Japanese font not found. Using default font. Japanese characters may not display correctly.")
            try:
                font = ImageFont.load_default(size=font_size) # Pillow 10.0.0以降
            except AttributeError: # 古いPillowでは size 引数がない
                 font = ImageFont.load_default()


        # テキスト描画位置と背景色の設定
        text_y_position = 10 # 左上からのYマージン
        line_spacing = 5      # 行間のスペース
        padding = 10          # テキスト背景のパディング

        for line in lines:
            # テキストの描画領域を計算
            if hasattr(font, 'getbbox'): # Pillow 9.2.0以降
                # (left, top, right, bottom)
                text_bbox = draw.textbbox((padding, text_y_position), line, font=font)
            else: # 古いPillow
                text_width, text_height = draw.textsize(line, font=font)
                text_bbox = (padding, text_y_position, padding + text_width, text_y_position + text_height)

            # 背景を描画 (各行ごと)
            bg_left = text_bbox[0] - padding
            bg_top = text_bbox[1] - padding
            bg_right = text_bbox[2] + padding
            bg_bottom = text_bbox[3] + padding
            
            draw.rectangle(
                (bg_left, bg_top, bg_right, bg_bottom),
                fill=(0, 0, 0, 180) # 半透明の黒色背景
            )
            
            # テキストを描画
            draw.text((padding, text_y_position), line, font=font, fill=(255, 255, 255)) # 白色テキスト
            
            # 次の行のY位置を更新
            text_y_position = bg_bottom + line_spacing


        # 画像をバイトデータに変換
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    except Exception as e:
        print(f"Error embedding text on image: {e}")
        # エラーが発生した場合でも、元の画像を返すか、エラーを示す画像を返すなどの処理も検討可能
        raise
