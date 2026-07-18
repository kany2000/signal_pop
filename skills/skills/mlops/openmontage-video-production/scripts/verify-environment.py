#!/usr/bin/env python3
"""
OpenMontage Environment Verification Script
Run this before starting any production to confirm all tools are available.
"""

import sys
import subprocess

def check_cmd(cmd, name):
    """Check if a command exists and get version."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"  ✅ {name}: {version}")
            return True
        else:
            print(f"  ❌ {name}: not found or error")
            return False
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return False

def check_python_import(module, name=None):
    """Check if a Python module can be imported."""
    try:
        __import__(module)
        print(f"  ✅ {name or module}: importable")
        return True
    except ImportError as e:
        print(f"  ❌ {name or module}: {e}")
        return False

def main():
    print("=" * 60)
    print("OpenMontage Environment Verification")
    print("=" * 60)
    
    all_ok = True
    
    print("\n🔧 System Dependencies:")
    all_ok &= check_cmd("ffmpeg -version", "FFmpeg")
    all_ok &= check_cmd("node --version", "Node.js")
    all_ok &= check_cmd("npm --version", "npm")
    all_ok &= check_cmd("python3 --version", "Python")
    
    # Check Node version >= 22 for HyperFrames
    try:
        result = subprocess.run("node --version", capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            version_str = result.stdout.strip().lstrip('v')
            major = int(version_str.split('.')[0])
            if major >= 22:
                print(f"  ✅ Node.js >= 22: v{version_str} (HyperFrames compatible)")
            else:
                print(f"  ⚠️  Node.js < 22: v{version_str} (HyperFrames needs >= 22)")
    except:
        pass
    
    print("\n🐍 Python Packages:")
    Packages:")
    all_ok &= check_python_import("tools.tool_registry", "OpenMontage tool_registry")
    all_ok &= check_python_import("remotion", "Remotion (if installed)")
    
    print("\n📁 Project Structure:")
    import os
    base = "/home/kan/shared/OpenMontage"
    for path in [
        "pipeline_defs/animation.yaml",
        "pipeline_defs/cinematic.yaml",
        "pipeline_defs/documentary-montage.yaml",
        "skills/pipelines/animation",
        "remotion-composer/package.json",
        "config.yaml",
        ".env",
    ]:
        full = os.path.join(base, path)
        if os.path.exists(full):
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path} (missing)")
            all_ok = False
    
    print("\n🎬 Tool Registry Capability Check:")
    try:
        sys.path.insert(0, base)
        from tools.tool_registry import registry
        registry.discover()
        summary = registry.provider_menu_summary()
        
        # Key capabilities
        caps = {c['capability']: c for c in summary['capabilities']}
        
        key_caps = [
            'image_generation',
            'video_generation', 
            'video_post',
            'tts',
            'music_search',
            'audio_processing',
            'graphics',
        ]
        
        for cap in key_caps:
            if cap in caps:
                c = caps[cap]
                avail = c['available_providers']
                unavail = c['unavailable_providers']
                print(f"  {cap}: {c['configured']}/{c['total']} ✅" if c['configured'] > 0 else f"  {cap}: {c['configured']}/{c['total']} ❌")
                if avail:
                    print(f"    Available: {', '.join(avail)}")
                if unavail:
                    print(f"    Need setup: {', '.join(unavail[:3])}{'...' if len(unavail) > 3 else ''}")
            else:
                print(f"  {cap}: NOT FOUND")
                all_ok = False
        
        # Composition runtimes
        print(f"\n  Composition runtimes:")
        for rt, available in summary['composition_runtimes'].items():
            status = "✅" if available else "❌"
            print(f"    {rt}: {status}")
            
    except Exception as e:
        print(f"  ❌ Registry check failed: {e}")
        all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ ALL CHECKS PASSED - Ready for production")
        return 0
    else:
        print("⚠️  SOME CHECKS FAILED - Review before production")
        return 1

if __name__ == "__main__":
    sys.exit(main())