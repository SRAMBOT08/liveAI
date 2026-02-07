#!/usr/bin/env python3
"""
LiveAI Quick Start Script
Helps start the system components in the correct order
"""
import subprocess
import sys
import time
import os
from pathlib import Path


def print_banner():
    print("=" * 70)
    print("  LiveAI Real-Time Market Risk Intelligence Platform")
    print("  Quick Start Script")
    print("=" * 70)
    print()


def check_kafka():
    """Check if Kafka is running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=kafka", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "kafka" in result.stdout.lower()
    except:
        return False


def start_kafka():
    """Start Kafka using Docker"""
    print("\n[1/3] Starting Kafka...")
    
    if check_kafka():
        print("✅ Kafka is already running")
        return True
    
    try:
        subprocess.run([
            "docker", "run", "-d",
            "--name", "liveai-kafka",
            "-p", "9092:9092",
            "apache/kafka:latest"
        ], check=True)
        
        print("⏳ Waiting for Kafka to be ready (30 seconds)...")
        time.sleep(30)
        
        print("✅ Kafka started successfully")
        return True
        
    except subprocess.CalledProcessError:
        print("❌ Failed to start Kafka")
        print("   Try: docker run -d --name liveai-kafka -p 9092:9092 apache/kafka:latest")
        return False


def start_producer():
    """Start market data producer"""
    print("\n[2/3] Starting Market Data Producer...")
    
    script = """
from kafka.producer_manager import producer_manager
import time

print("Initializing producer...")
if producer_manager.initialize():
    print("Starting streaming...")
    producer_manager.start_streaming()
    print("✅ Producer is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping producer...")
        producer_manager.shutdown()
else:
    print("❌ Failed to initialize producer")
"""
    
    try:
        # Write temporary script
        script_path = Path("_temp_producer.py")
        script_path.write_text(script)
        
        # Start in background
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Producer started successfully (PID: {})".format(process.pid))
            return True
        else:
            print("❌ Producer failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting producer: {e}")
        return False


def start_dashboard():
    """Start Streamlit dashboard"""
    print("\n[3/3] Starting Streamlit Dashboard...")
    
    try:
        print("🚀 Launching dashboard at http://localhost:8501")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "dashboard/app.py",
            "--server.port=8501",
            "--server.headless=true"
        ])
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down dashboard...")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")


def main():
    print_banner()
    
    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found")
        print("   Copy .env.example to .env and configure API keys")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Start components
    if not start_kafka():
        sys.exit(1)
    
    # Note: In production, you'd want separate terminals
    # For this starter script, we'll just guide the user
    
    print("\n" + "=" * 70)
    print("  Setup Complete!")
    print("=" * 70)
    print()
    print("To complete the startup, run these commands in separate terminals:")
    print()
    print("Terminal 1 (Producer):")
    print("  python -c \"from kafka.producer_manager import producer_manager; " +
          "producer_manager.initialize(); producer_manager.start_streaming(); " +
          "input('Press Enter to stop...')\"")
    print()
    print("Terminal 2 (Pathway Engine):")
    print("  python app.py")
    print()
    print("Terminal 3 (Dashboard):")
    print("  streamlit run dashboard/app.py")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
