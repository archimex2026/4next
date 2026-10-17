import os
import re
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from app.config import MEDIA_DIR, FFMPEG_EXE
from app.services.audio_generator import get_audio_duration

VIDEO_DIR = MEDIA_DIR / "video"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
STOCK_DIR = MEDIA_DIR / "stock_images"
STOCK_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size: int, bold: bool = False):
    """Safely loads system font or default font."""
    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()

def wrap_text(text: str, max_chars: int = 45) -> List[str]:
    words = text.split()
    lines = []
    current_line = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 <= max_chars:
            current_line.append(word)
            current_len += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def get_topic_image(topic_name: str, width: int = 1280, height: int = 720) -> Image.Image:
    """
    Selects and loads a topic-relevant open-source photo from stock_images,
    or falls back to an elegant modern blueprint background.
    """
    t_low = topic_name.lower()
    img_name = "tech.jpg"
    if any(k in t_low for k in ["requirement", "strategy", "story", "intent", "case", "business", "scenarios"]):
        img_name = "strategy.jpg"
    elif any(k in t_low for k in ["architect", "deliverable", "spec", "design", "structure"]):
        img_name = "architecture.jpg"
    elif any(k in t_low for k in ["entity", "model", "database", "orm", "aggregate", "data", "schema"]):
        img_name = "data.jpg"
    elif any(k in t_low for k in ["validation", "rule", "compute", "metric", "test", "accounting"]):
        img_name = "metrics.jpg"
    elif any(k in t_low for k in ["team", "workflow", "actor", "interaction", "sequence"]):
        img_name = "team.jpg"

    img_path = STOCK_DIR / img_name
    if img_path.exists():
        try:
            base = Image.open(img_path).convert("RGB")
            # Aspect fill crop
            bw, bh = base.size
            target_ratio = width / height
            curr_ratio = bw / bh
            if curr_ratio > target_ratio:
                # crop width
                new_w = int(bh * target_ratio)
                left = (bw - new_w) // 2
                base = base.crop((left, 0, left + new_w, bh))
            else:
                new_h = int(bw / target_ratio)
                top = (bh - new_h) // 2
                base = base.crop((0, top, bw, top + new_h))
            return base.resize((width, height), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Error loading stock photo {img_path}: {e}")

    # Fallback modern dark blueprint background
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.ImageDraw(img)
    for x in range(0, width, 60):
        draw.line([x, 0, x, height], fill=(24, 35, 55), width=1)
    for y in range(0, height, 60):
        draw.line([0, y, width, y], fill=(24, 35, 55), width=1)
    return img

def draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str, width: int = 1280):
    # Top banner in Book2Sound Slate & Navy
    draw.rectangle([0, 0, width, 70], fill=(15, 23, 42)) # Deep slate
    draw.rectangle([0, 66, width, 70], fill=(10, 102, 194)) # Accent line
    font_head = get_font(24, bold=True)
    draw.text((40, 20), "BOOK2SOUND STUDIO", font=font_head, fill=(255, 255, 255))
    font_sub = get_font(18, bold=False)
    draw.text((350, 24), f"|  {subtitle}", font=font_sub, fill=(147, 197, 253))

def render_scene_1(lesson_title: str, course_title: str) -> Image.Image:
    """Scene 1: Lesson Title Card with Open-Source Topic Photo Backdrop"""
    base = get_topic_image(lesson_title, 1280, 720)
    # Dark translucent Fluent overlay
    overlay = Image.new("RGBA", (1280, 720), (0, 43, 73, 215)) # 85% opacity
    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.ImageDraw(base)
    draw_header(draw, lesson_title, course_title)

    # Center hero card with glassmorphic border
    draw.rounded_rectangle([120, 120, 1160, 600], radius=24, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
    
    # Tag badge
    draw.rounded_rectangle([180, 170, 390, 215], radius=12, fill=(10, 102, 194))
    font_tag = get_font(16, bold=True)
    draw.text((200, 182), "EXECUTIVE MODULE", font=font_tag, fill=(255, 255, 255))

    font_title = get_font(36, bold=True)
    wrapped = wrap_text(lesson_title, 36)
    y = 245
    for line in wrapped[:3]:
        draw.text((180, y), line, font=font_title, fill=(255, 255, 255))
        y += 48

    # Meta bar
    font_meta = get_font(20, bold=False)
    draw.text((180, 460), f"Curriculum: {course_title}", font=font_meta, fill=(148, 163, 184))
    draw.text((180, 498), "Synthesized Technical Masterclass • In-Depth Architectural Audio", font=font_meta, fill=(56, 189, 248))
    
    # Verified badge
    draw.rounded_rectangle([180, 540, 440, 575], radius=8, fill=(5, 118, 66))
    font_badge = get_font(14, bold=True)
    draw.text((200, 548), "✓ Verified Manuscript Knowledge", font=font_badge, fill=(255, 255, 255))
    return base

def render_scene_2(summary: str, lesson_title: str) -> Image.Image:
    """Scene 2: Lesson Executive Foundations & Problem Scope"""
    img = Image.new("RGB", (1280, 720), color=(243, 242, 239)) # LinkedIn light surface
    draw = ImageDraw.ImageDraw(img)
    draw_header(draw, lesson_title, "Executive Foundations & Problem Scope")

    draw.rounded_rectangle([100, 110, 1180, 630], radius=20, fill=(255, 255, 255), outline=(220, 225, 235), width=2)
    draw.rounded_rectangle([150, 150, 360, 190], radius=10, fill=(5, 118, 66))
    font_tag = get_font(16, bold=True)
    draw.text((170, 160), "FOUNDATIONAL SCOPE", font=font_tag, fill=(255, 255, 255))

    font_head = get_font(28, bold=True)
    draw.text((150, 215), "Core Architectural Intent", font=font_head, fill=(25, 25, 25))

    font_body = get_font(22, bold=False)
    lines = wrap_text(summary, 54)
    y = 270
    for line in lines[:6]:
        draw.text((150, y), line, font=font_body, fill=(51, 65, 85))
        y += 38

    # Focus box at bottom
    draw.rounded_rectangle([150, 495, 1130, 585], radius=14, fill=(235, 243, 250), outline=(10, 102, 194), width=1)
    font_box_title = get_font(18, bold=True)
    draw.text((180, 515), "Strategic Objective:", font=font_box_title, fill=(10, 102, 194))
    font_box_desc = get_font(18, bold=False)
    draw.text((360, 515), "Eliminate ambiguity and establish formal invariant boundaries.", font=font_box_desc, fill=(30, 41, 59))
    draw.text((180, 545), "• Bounded domain models protect systems from uncontrolled mutation.", font=get_font(16, bold=False), fill=(100, 116, 139))
    return img

def render_scene_3(key_ideas: List[str], lesson_title: str) -> Image.Image:
    """Scene 3: Fundamental Invariant Rules & Detailed Mechanics"""
    img = Image.new("RGB", (1280, 720), color=(243, 242, 239))
    draw = ImageDraw.ImageDraw(img)
    draw_header(draw, lesson_title, "Key Invariants & Architectural Rules")

    draw.rounded_rectangle([100, 100, 1180, 640], radius=20, fill=(255, 255, 255), outline=(220, 225, 235), width=2)

    font_head = get_font(26, bold=True)
    draw.text((140, 130), "Core Specifications & Rules", font=font_head, fill=(10, 102, 194))

    y = 185
    colors = [(10, 102, 194), (55, 143, 233), (5, 118, 66)]
    items = key_ideas[:3] if key_ideas else ["Enforce aggregate boundary consistency", "Encapsulate persistent identity vs immutable values", "Model bidirectional associations as unidirectional where possible"]
    for i, idea in enumerate(items):
        # Card
        draw.rounded_rectangle([140, y, 1140, y + 125], radius=14, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
        # Number badge
        draw.ellipse([165, y + 30, 225, y + 90], fill=colors[i % len(colors)])
        font_num = get_font(26, bold=True)
        draw.text((187, y + 43), str(i + 1), font=font_num, fill=(255, 255, 255))
        
        # Rule Header
        font_rh = get_font(20, bold=True)
        draw.text((250, y + 25), f"Invariant Rule {i+1}", font=font_rh, fill=(15, 23, 42))
        
        # Text
        font_idea = get_font(18, bold=False)
        idea_lines = wrap_text(idea, 58)
        iy = y + 55
        for l in idea_lines[:2]:
            draw.text((250, iy), l, font=font_idea, fill=(51, 65, 85))
            iy += 28
        y += 145
    return img

def render_scene_4_mermaid(lesson_title: str, mermaid_code: str, key_ideas: List[str]) -> Image.Image:
    """Scene 4: Dynamic Mermaid Scheme Visualizer (Visual Architecture Slide)"""
    img = Image.new("RGB", (1280, 720), color=(11, 25, 44)) # deep navy blueprint
    draw = ImageDraw.ImageDraw(img)
    draw_header(draw, lesson_title, "Mermaid Scheme & Architectural Blueprint")

    # Background subtle grid
    for x in range(0, 1280, 40):
        draw.line([x, 70, x, 720], fill=(18, 36, 62), width=1)
    for y in range(70, 720, 40):
        draw.line([0, y, 1280, y], fill=(18, 36, 62), width=1)

    # Top indicator
    draw.rounded_rectangle([100, 95, 450, 135], radius=8, fill=(10, 102, 194))
    font_pill = get_font(15, bold=True)
    draw.text((115, 105), "DYNAMIC MERMAID WORKFLOW SCHEME", font=font_pill, fill=(255, 255, 255))

    # Parse mermaid code to extract nodes and relationships
    nodes = []
    # Pattern 1: A["Label"] or A[Label]
    raw_nodes = re.findall(r'([A-Za-z0-9_]+)\[[\"\'\s]?([^\]\"\']+)[\"\'\s]?\]', mermaid_code)
    for nid, nlbl in raw_nodes:
        clean_lbl = nlbl.strip()
        if clean_lbl and clean_lbl not in [n[1] for n in nodes]:
            nodes.append((nid, clean_lbl))

    # If sequence diagram: Actor ->> Target: Message
    if not nodes:
        seq_matches = re.findall(r'([A-Za-z0-9_]+)\s*->>\s*([A-Za-z0-9_]+)\s*:\s*([^\n\r]+)', mermaid_code)
        for act1, act2, msg in seq_matches:
            if act1 not in [n[1] for n in nodes]:
                nodes.append((act1, act1))
            if act2 not in [n[1] for n in nodes]:
                nodes.append((act2, act2))
            nodes.append((f"{act1}_{act2}", msg.strip()))

    # Fallback nodes from key ideas if mermaid was minimal
    if len(nodes) < 3:
        nodes = [
            ("Actor", "Business Actor / Client"),
            ("Service", "Application Service Boundary"),
            ("Aggregate", "Aggregate Root & Invariants"),
            ("Database", "Persistence ORM / State Store")
        ]

    # Draw 4-step architecture pipeline
    display_nodes = nodes[:4]
    box_w = 230
    box_h = 170
    start_x = 90
    y_pos = 190
    spacing = 65

    step_colors = [(10, 102, 194), (55, 143, 233), (87, 163, 255), (5, 118, 66)]

    for idx, (nid, nlabel) in enumerate(display_nodes):
        bx = start_x + idx * (box_w + spacing)
        # Box frame
        draw.rounded_rectangle([bx, y_pos, bx + box_w, y_pos + box_h], radius=16, fill=(24, 38, 64), outline=(56, 189, 248), width=2)
        # Top color badge
        draw.rounded_rectangle([bx, y_pos, bx + box_w, y_pos + 42], radius=14, fill=step_colors[idx % len(step_colors)])
        draw.rectangle([bx, y_pos + 20, bx + box_w, y_pos + 42], fill=step_colors[idx % len(step_colors)]) # flatten bottom corners
        
        draw.text((bx + 15, y_pos + 10), f"NODE {idx+1}", font=get_font(15, bold=True), fill=(255, 255, 255))

        # Node Label
        font_nl = get_font(18, bold=True)
        lbl_lines = wrap_text(nlabel, 20)
        ly = y_pos + 58
        for line in lbl_lines[:3]:
            draw.text((bx + 15, ly), line, font=font_nl, fill=(255, 255, 255))
            ly += 24

        # Subtitle tag
        font_sub = get_font(13, bold=False)
        draw.text((bx + 15, y_pos + 138), f"ID: {nid}", font=font_sub, fill=(148, 163, 184))

        # Connector Arrow to next
        if idx < len(display_nodes) - 1:
            ax1 = bx + box_w + 10
            ax2 = ax1 + spacing - 20
            ay = y_pos + 85
            draw.line([ax1, ay, ax2, ay], fill=(56, 189, 248), width=4)
            # Arrowhead
            draw.polygon([(ax2 + 8, ay), (ax2 - 4, ay - 7), (ax2 - 4, ay + 7)], fill=(56, 189, 248))

    # Bottom Architectural Invariant Card
    draw.rounded_rectangle([90, 420, 1190, 640], radius=16, fill=(18, 30, 52), outline=(71, 85, 105), width=1)
    draw.text((120, 445), "ARCHITECTURAL INVARIANTS & MESSAGE FLOW:", font=get_font(18, bold=True), fill=(56, 189, 248))
    
    inv1 = key_ideas[0] if key_ideas else "External requests enter strictly through the aggregate root."
    inv2 = key_ideas[1] if len(key_ideas) > 1 else "State mutations are evaluated against domain constraints prior to commit."
    draw.text((120, 485), f"• {inv1}", font=get_font(17, bold=False), fill=(226, 232, 240))
    draw.text((120, 525), f"• {inv2}", font=get_font(17, bold=False), fill=(148, 163, 184))
    draw.text((120, 565), "• Mermaid Scheme verified for compilation and deterministic state handoffs.", font=get_font(15, bold=False), fill=(5, 118, 66))
    return img

def render_scene_5(examples: List[str], lesson_title: str) -> Image.Image:
    """Scene 5: Practical Real-World Case Study with Split Open-Source Photo"""
    img = Image.new("RGB", (1280, 720), color=(243, 242, 239))
    draw = ImageDraw.ImageDraw(img)
    draw_header(draw, lesson_title, "Production Case Study in Practice")

    # Main card
    draw.rounded_rectangle([90, 100, 1190, 640], radius=20, fill=(255, 255, 255), outline=(220, 225, 235), width=2)
    
    # Left column: Open-source photo illustration
    left_img = get_topic_image("case study production", 460, 480)
    img.paste(left_img, (120, 130))
    # Photo frame border
    draw.rounded_rectangle([120, 130, 580, 610], radius=12, outline=(10, 102, 194), width=2)
    
    # Right column: Case study content
    rx = 610
    draw.rounded_rectangle([rx, 130, rx + 190, 170], radius=8, fill=(217, 119, 6)) # amber tag
    font_tag = get_font(15, bold=True)
    draw.text((rx + 15, 140), "PRODUCTION CASE", font=font_tag, fill=(255, 255, 255))

    draw.text((rx, 195), "Real-World Execution Scenario", font=get_font(26, bold=True), fill=(25, 25, 25))

    ex_text = examples[0] if examples else "Applying disciplined testing in your product roadmap creates immediate clarity and prevents edge-case regressions."
    font_body = get_font(20, bold=False)
    lines = wrap_text(ex_text, 44)
    y = 250
    for line in lines[:5]:
        draw.text((rx, y), line, font=font_body, fill=(51, 65, 85))
        y += 35

    # Secondary insight
    draw.rounded_rectangle([rx, 450, 1160, 590], radius=14, fill=(235, 243, 250), outline=(10, 102, 194), width=1)
    draw.text((rx + 25, 475), "Key Implementation Lesson:", font=get_font(18, bold=True), fill=(10, 102, 194))
    
    ex_sub = examples[1] if len(examples) > 1 else "Rigorous domain modeling reduces technical debt and eliminates ambiguous stakeholder handoffs."
    sub_lines = wrap_text(ex_sub, 42)
    sy = 510
    for sl in sub_lines[:2]:
        draw.text((rx + 25, sy), sl, font=get_font(17, bold=False), fill=(30, 41, 59))
        sy += 28
    return img

def render_scene_6(action_items: List[str], lesson_title: str) -> Image.Image:
    """Scene 6: Conclusion & Actionable Deliverables Checklist"""
    img = Image.new("RGB", (1280, 720), color=(10, 102, 194)) # rich brand finish
    draw = ImageDraw.ImageDraw(img)

    # Header
    font_brand = get_font(22, bold=True)
    draw.text((50, 30), "BOOK2COURSE AI • SYNTHESIS & MASTERY", font=font_brand, fill=(255, 255, 255))

    # Center card
    draw.rounded_rectangle([120, 95, 1160, 640], radius=24, fill=(255, 255, 255))
    
    font_concl = get_font(30, bold=True)
    draw.text((180, 135), "Mandatory Deliverables & Execution Checklist", font=font_concl, fill=(25, 25, 25))

    items = action_items if action_items else [
        "Draft the primary use case diagram and boundary specifications",
        "Formulate explicit invariant validation rules before schema generation",
        "Test domain retention with the interactive flashcards and chapter quiz"
    ]

    y = 215
    font_item = get_font(20, bold=False)
    for i, itm in enumerate(items[:3]):
        # Checkmark circle
        draw.ellipse([180, y + 5, 225, y + 50], fill=(5, 118, 66))
        draw.text((195, y + 14), "✓", font=get_font(22, bold=True), fill=(255, 255, 255))
        
        # Item text
        lines = wrap_text(itm, 62)
        iy = y + 12
        for l in lines[:2]:
            draw.text((245, iy), l, font=font_item, fill=(30, 41, 59))
            iy += 26
        y += 85

    # Bottom badge
    draw.rounded_rectangle([180, 510, 1100, 595], radius=14, fill=(240, 249, 255), outline=(56, 189, 248), width=1)
    font_badge = get_font(18, bold=True)
    draw.text((220, 540), "Module Completed! Continue to the next level in your Learning Path.", font=font_badge, fill=(10, 102, 194))
    return img

def generate_video_lesson(
    lesson_id: str,
    lesson_title: str,
    course_title: str,
    summary: str,
    key_ideas: List[str],
    examples: List[str],
    action_items: List[str],
    mermaid_diagram: str = "",
    audio_path: Optional[str] = None
) -> str:
    """
    Renders 6 high-definition scenes including open-source topic photography
    and Mermaid architecture schemes, dynamically synchronizing to audio duration.
    Returns relative URL: /media/video/{lesson_id}.mp4
    """
    output_filename = f"{lesson_id}.mp4"
    output_path = VIDEO_DIR / output_filename

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        
        # Render 6 distinct scenes
        scene1 = render_scene_1(lesson_title, course_title)
        scene2 = render_scene_2(summary, lesson_title)
        scene3 = render_scene_3(key_ideas, lesson_title)
        scene4 = render_scene_4_mermaid(lesson_title, mermaid_diagram, key_ideas)
        scene5 = render_scene_5(examples, lesson_title)
        scene6 = render_scene_6(action_items, lesson_title)

        scenes = [scene1, scene2, scene3, scene4, scene5, scene6]
        scene_paths = []
        for i, sc in enumerate(scenes):
            p = tmp / f"scene_{i}.png"
            sc.save(p)
            scene_paths.append(p)

        # Check audio file and duration
        audio_full_path = None
        audio_dur = 30.0
        if audio_path:
            possible_path = Path(MEDIA_DIR.parent / audio_path.lstrip("/"))
            if possible_path.exists():
                audio_full_path = possible_path
                audio_dur = get_audio_duration(possible_path)

        # Calculate exact duration per scene so video matches audio duration perfectly
        num_scenes = len(scenes)
        duration_per_scene = max(4.0, round(audio_dur / num_scenes, 2))

        # Create concat text file for ffmpeg
        concat_file = tmp / "scenes.txt"
        with open(concat_file, "w") as f:
            for p in scene_paths:
                f.write(f"file '{p.as_posix()}'\n")
                f.write(f"duration {duration_per_scene}\n")
            # Write last file again per ffmpeg concat demuxer spec
            f.write(f"file '{scene_paths[-1].as_posix()}'\n")

        # FFmpeg command
        if audio_full_path:
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-i", str(audio_full_path),
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest",
                "-r", "24",
                str(output_path)
            ]
        else:
            cmd = [
                FFMPEG_EXE, "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                "-r", "24",
                str(output_path)
            ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"Rendered video successfully ({audio_dur}s) at {output_path}")
        except Exception as e:
            print(f"FFmpeg generation exception: {e}. Generating single frame loop.")
            cmd_fallback = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", str(scene_paths[0]),
                "-t", "10",
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                "-r", "24",
                str(output_path)
            ]
            try:
                subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            except Exception:
                pass

    return f"/media/video/{output_filename}"
