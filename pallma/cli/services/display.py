#!/usr/bin/env python3
"""
Simple display command for real-time Kafka message statistics.
Uses built-in Kafka tools instead of external dependencies.
"""

import json
import signal
import subprocess
from collections import defaultdict
from datetime import datetime

import typer


class KafkaStatsDisplay:
    def __init__(self):
        self.total_messages = 0
        self.decisions = defaultdict(int)
        self.running = True

    def process_message(self, message_line):
        """Process a message line from kafka-console-consumer"""
        try:
            # Parse the JSON message
            message_data = json.loads(message_line.strip())
            self.total_messages += 1
            
            # Extract decisions from the message
            decisions = message_data.get("decisions", [])
            for decision in decisions:
                self.decisions[decision] += 1
            
            # Calculate percentages
            total_decisions = sum(self.decisions.values())
            allow_percentage = (self.decisions.get('allow', 0) / total_decisions * 100) if total_decisions > 0 else 0
            block_percentage = (self.decisions.get('block', 0) / total_decisions * 100) if total_decisions > 0 else 0
            
            # Display stats
            self.display_stats(allow_percentage, block_percentage)
            
        except json.JSONDecodeError:
            # Skip invalid JSON messages
            pass
        except Exception as e:
            typer.echo(f"❌ Error processing message: {e}")

    def display_stats(self, allow_percentage, block_percentage):
        """Display current statistics"""
        # Clear screen
        print("\033[2J\033[H", end="")
        
        # Display header
        print("=" * 60)
        print("           PALLMA REAL-TIME STATISTICS")
        print("=" * 60)
        print()
        
        # Display total messages
        print(f"📊 Total Messages: {self.total_messages}")
        print()
        
        # Display decision counts
        print("📈 Decision Distribution:")
        print(f"   ✅ Allow: {self.decisions.get('allow', 0)}")
        print(f"   ❌ Block: {self.decisions.get('block', 0)}")
        print()
        
        # Display percentages
        print("📊 Percentages:")
        print(f"   ✅ Allow: {allow_percentage:.1f}%")
        print(f"   ❌ Block: {block_percentage:.1f}%")
        print()
        
        # Display timestamp
        print(f"🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("Press Ctrl+C to exit")
        print("=" * 60)

    def consume_messages(self):
        """Consume messages using kafka-console-consumer"""
        try:
            # Start kafka-console-consumer process
            cmd = [
                "docker", "exec", "pallma-kafka", 
                "kafka-console-consumer", 
                "--bootstrap-server", "localhost:9092",
                "--topic", "output-topic",
                "--from-beginning"
            ]
            
            typer.echo("🎯 Connecting to Kafka. Waiting for messages...")
            typer.echo("📊 Statistics will update in real-time as messages arrive.")
            typer.echo()
            
            # Show initial stats
            self.display_stats(0, 0)
            
            # Start the consumer process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in process.stdout:
                if not self.running:
                    break
                    
                if line.strip():
                    self.process_message(line)
                    
        except KeyboardInterrupt:
            typer.echo("\n🛑 Shutting down...")
        except Exception as e:
            typer.echo(f"❌ Error: {e}")
        finally:
            if 'process' in locals():
                process.terminate()
                process.wait()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        typer.echo("\n🛑 Shutting down...")
        self.running = False


def display_stats():
    """Main function to display real-time statistics"""
    # Check if Kafka is running
    try:
        result = subprocess.run(
            ["docker", "exec", "pallma-kafka", "kafka-topics", "--bootstrap-server", "localhost:9092", "--list"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            typer.echo("❌ Error: Kafka is not running. Please start the services first with 'pallma start'")
            raise typer.Exit(1)
    except Exception as e:
        typer.echo("❌ Error: Cannot connect to Kafka. Make sure the services are running.")
        typer.echo("💡 Run 'pallma start' to start all services")
        raise typer.Exit(1)

    # Create display instance
    display = KafkaStatsDisplay()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, display.signal_handler)
    signal.signal(signal.SIGTERM, display.signal_handler)
    
    # Start consuming messages
    try:
        display.consume_messages()
    except KeyboardInterrupt:
        typer.echo("\n👋 Goodbye!")


if __name__ == "__main__":
    display_stats() 