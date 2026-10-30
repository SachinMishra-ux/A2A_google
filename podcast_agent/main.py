"""Entry Point for Podcast Agent (Google ADK).

This script serves as the direct entry point for executing the Podcast Agent
either interactively or programmatically.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load local environment variables (.env)
load_dotenv()

from podcast_agent.agent import root_agent
from podcast_agent.schemas import PodcastPlan, SpeakerProfile, PodcastScript, DialogueTurn

def inspect_agent():
    """Prints diagnostic information about the ADK Podcast Agent tree."""
    print("=" * 65)
    print(" 🎙️  PODCAST STUDIO AGENT (GOOGLE ADK) - ARCHITECTURE INSPECTION")
    print("=" * 65)
    print(f"Agent Name:        {root_agent.name}")
    print(f"Model:             {root_agent.model}")
    print(f"Description:       {root_agent.description}")
    print("\nTools Registered:")
    for t in root_agent.tools:
        name = getattr(t, "__name__", str(t))
        print(f"  • {name}")
    print("\nSub-Agents in Coordinator Hierarchy:")
    for sa in root_agent.sub_agents:
        print(f"  • {sa.name:<22} (Model: {sa.model})")
        print(f"    Description: {sa.description[:75]}...")
    print("=" * 65)

def run_dry_run_generation(topic: str):
    """Simulates podcast generation without live API calls if no key is set."""
    print(f"\n[DEMO MODE] Generating sample podcast outline for topic: '{topic}'\n")
    plan = PodcastPlan(
        episode_title=f"The Future of {topic}: Architectural Deep Dive",
        target_audience="Developers and AI Engineers",
        core_topics=[f"Evolution of {topic}", "Real-world trade-offs", "Production deployment strategies"],
        speaker_count=2,
        speaker_profiles=[
            SpeakerProfile(name="Alex", role="Host", tone="Energetic, curious", voice_id="en-US-GuyNeural"),
            SpeakerProfile(name="Morgan", role="Expert", tone="Authoritative, analytical", voice_id="en-US-JennyNeural")
        ]
    )
    
    script = PodcastScript(
        episode_title=plan.episode_title,
        speaker_count=2,
        turns=[
            DialogueTurn(speaker="Alex", text=f"Welcome back to AI Architecture Daily! Today we are dissecting {topic}."),
            DialogueTurn(speaker="Morgan", text="Thanks Alex. What makes this topic particularly fascinating is how it bridges theory and production scalability."),
            DialogueTurn(speaker="Alex", text="Exactly. Let's break down the technical implications step by step.")
        ]
    )
    
    print(f"Title: {plan.episode_title}")
    print(f"Hosts: {', '.join([s.name + ' (' + s.role + ')' for s in plan.speaker_profiles])}")
    print("\nGenerated Script Sample:")
    for turn in script.turns:
        print(f"  [{turn.speaker}]: {turn.text}")
    print("\n✅ Dry run completed successfully!")

async def run_live_agent(prompt: str):
    """Runs the live Google ADK agent using InMemoryRunner."""
    from google.adk.runners import InMemoryRunner
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("\n⚠️  No GEMINI_API_KEY or GOOGLE_API_KEY found in environment.")
        print("Falling back to structural dry-run demonstration.")
        run_dry_run_generation(prompt)
        return

    print(f"\n🚀 Running Live Podcast Agent with prompt: '{prompt}'...")
    runner = InMemoryRunner(agent=root_agent)
    # Execute runner turn
    response = await runner.run_debug(prompt)
    print("\n=== AGENT RESPONSE ===")
    print(response)

def main():
    parser = argparse.ArgumentParser(description="Podcast Agent Entry Point (Google ADK)")
    parser.add_argument("--topic", type=str, default="A2A Protocol & Multi-Agent Collaboration", help="Podcast topic or prompt")
    parser.add_argument("--inspect", action="store_true", help="Print agent architectural inspection")
    parser.add_argument("--dry-run", action="store_true", help="Run simulated generation without calling Gemini API")
    args = parser.parse_args()

    inspect_agent()

    if args.dry_run or ("GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ):
        run_dry_run_generation(args.topic)
    else:
        asyncio.run(run_live_agent(args.topic))

if __name__ == "__main__":
    main()
