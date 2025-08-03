import typer
import subprocess
import os
import sys

app = typer.Typer()

@app.command()
def start():
    """Build and start all services using docker-compose"""
    # Get the directory containing docker-compose.yml
    compose_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cli")
    
    # Set environment variable for the CLI root directory
    env = os.environ.copy()
    env['PALLMA_CLI_ROOT'] = compose_dir
    
    # Create the external network if it doesn't exist
    typer.echo("Creating external network if it doesn't exist...")
    network_cmd = "docker network create pallma-network"
    try:
        subprocess.run(network_cmd, shell=True, check=True)
        typer.echo("Network 'pallma-network' created successfully.")
    except subprocess.CalledProcessError:
        typer.echo("Network 'pallma-network' already exists or could not be created.")
    
    # Build all services first
    typer.echo("Building all services...")
    build_cmd = "docker-compose build"
    typer.echo(f"Running: {build_cmd}")
    subprocess.run(build_cmd, shell=True, check=True, cwd=compose_dir, env=env)
    
    # Start all services
    typer.echo("Starting all services...")
    up_cmd = "docker-compose -p pallma up -d"
    typer.echo(f"Running: {up_cmd}")
    subprocess.run(up_cmd, shell=True, check=True, cwd=compose_dir, env=env)
    
    typer.echo("All services are starting up. Use 'docker-compose logs -f' to view logs.")

@app.command()
def stop():
    """Stop all services using docker-compose"""
    # Get the directory containing docker-compose.yml
    compose_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cli")
    
    # Set environment variable for the CLI root directory
    env = os.environ.copy()
    env['PALLMA_CLI_ROOT'] = compose_dir
    
    # Stop all services
    typer.echo("Stopping all services...")
    stop_cmd = "docker-compose -p pallma down"
    typer.echo(f"Running: {stop_cmd}")
    subprocess.run(stop_cmd, shell=True, check=True, cwd=compose_dir, env=env)
    
    # Remove the external network if it exists and no containers are using it
    typer.echo("Cleaning up external network...")
    cleanup_cmd = "docker network rm pallma-network"
    try:
        subprocess.run(cleanup_cmd, shell=True, check=True)
        typer.echo("Network 'pallma-network' removed successfully.")
    except subprocess.CalledProcessError:
        typer.echo("Network 'pallma-network' could not be removed (may be in use or not exist).")
    
    typer.echo("All services have been stopped.")


@app.command()
def display():
    """Display real-time statistics from Kafka messages"""
    
    # Add the CLI directory to the path so we can import the display module
    cli_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cli")
    sys.path.insert(0, cli_dir)
    
    try:
        from pallma.cli.services.display import display_stats
        display_stats()
    except ImportError as e:
        typer.echo(f"❌ Error importing display module: {e}")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Error running display: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
