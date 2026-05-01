#!/usr/bin/env python3
"""
Leonardo.ai 圖像生成腳本
用法: python3 leonardo_gen.py "prompt文字" [num_images] [model_id]
"""

import os, sys, json, time, urllib.request, urllib.error

# Load API key
API_KEY = None
with open(os.path.expanduser("~/.api_keys")) as f:
    for line in f:
        if line.startswith("LEONARDO_API_KEY="):
            API_KEY = line.split("=", 1)[1].strip()
            break

if not API_KEY:
    print("❌ LEONARDO_API_KEY not found in ~/.api_keys")
    sys.exit(1)

API_BASE = "https://cloud.leonardo.ai/api/rest/v1"

def make_request(method, path, data=None):
    url = f"{API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers=headers,
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"❌ HTTP {e.code}: {error_body[:500]}")
        sys.exit(1)

def generate(prompt, num_images=1, model_id=None,
             width=1024, height=1024, guidance_scale=7, steps=30):
    """發送生成請求"""
    print(f"🎨 生成圖片中...")
    print(f"   Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    
    payload = {
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, watermark, text, logo",
        "num_images": num_images,
        "width": width,
        "height": height,
        "guidance_scale": guidance_scale,
        "num_inference_steps": steps
    }
    if model_id:
        payload["model_id"] = model_id
    result = make_request("POST", "/generations", payload)
    gen_id = result.get("sdGenerationJob", {}).get("generationId")
    if not gen_id:
        print("❌ 無法取得 generationId")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)
    print(f"   Generation ID: {gen_id}")
    return gen_id

def wait_and_get(gen_id, timeout=120, poll_interval=5):
    """等待生成完成並取得結果"""
    print(f"⏳ 等待生成中 (最多 {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        result = make_request("GET", f"/generations/{gen_id}")
        status = result.get("generations_by_pk", {}).get("status", "UNKNOWN")
        print(f"   狀態: {status}")
        if status == "COMPLETE":
            images = result["generations_by_pk"]["generated_images"]
            urls = [img["url"] for img in images]
            print(f"✅ 完成！取得 {len(urls)} 張圖片")
            return urls
        elif status in ("FAILED", "CANCELLED"):
            print(f"❌ 生成失敗: {status}")
            sys.exit(1)
        time.sleep(poll_interval)
    print(f"⏰ 等待超時 ({timeout}s)")
    sys.exit(1)

def download_images(urls, output_dir="/home/jhe/.openclaw/workspace/posters"):
    """下載圖片到本地"""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for i, url in enumerate(urls):
        filename = f"leonardo_{int(time.time())}_{i+1}.jpg"
        path = os.path.join(output_dir, filename)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(path, "wb") as f:
                f.write(data)
            print(f"   📥 {path} ({len(data)//1024}KB)")
            paths.append(path)
        except Exception as e:
            print(f"   ⚠️ 下載失敗 {url}: {e}")
    return paths

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else input("輸入 prompt: ").strip()
    if not prompt:
        print("❌ prompt 不能為空")
        sys.exit(1)
    
    num_images = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    model_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    gen_id = generate(prompt, num_images, model_id)
    urls = wait_and_get(gen_id)
    paths = download_images(urls)
    
    print("\n✅ 完成！")
    for p in paths:
        print(f"   {p}")
    print(f"\n📎 URLs:")
    for url in urls:
        print(f"   {url}")
