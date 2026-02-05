"""Main entry point - Interactive chat interface for the clinical trials agent"""

try:
    from .agent import Agent
    from .logger import ConversationLogger
except ImportError:
    from agent import Agent
    from logger import ConversationLogger


def main():
    """Run interactive chat shell with memory"""
    print("=" * 60)
    print("🏥 Clinical Trials Feasibility Assistant")
    print("=" * 60)
    print("Ask questions about clinical trials from ClinicalTrials.gov")
    print("Commands: 'exit' to leave, 'clear' to reset memory\n")
    
    # Initialize logger
    logger = ConversationLogger()
    print(f"📝 Logging to: {logger.get_session_file()}\n")
    
    agent = Agent(logger=logger)
    
    while True:
        try:
            user_input = input(">>> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == "clear":
                agent.clear_memory()
                print("🧹 Memory cleared!\n")
                continue
            
            response = agent.run(user_input)
            # TODO : understund this part of the code
            # Handle string response (when no tools called)
            if isinstance(response, str):
                print(f"\n📝 Answer:\n{response}\n")
            else:
                print(f"\n📝 Answer:\n{response.answer}\n")
                
                if response.trials:
                    print("🔬 Trials:")
                    for t in response.trials:
                        print(f"  • **{t.nct_id}** - {t.title}")
                        details = []
                        if t.phase:
                            details.append(f"Phase: {t.phase}")
                        if t.status:
                            details.append(f"Status: {t.status}")
                        if t.sponsor:
                            details.append(f"Sponsor: {t.sponsor}")
                        if t.enrollment:
                            details.append(f"Enrollment: {t.enrollment}")
                        if details:
                            print(f"    {' | '.join(details)}")
                        if t.start_date or t.completion_date:
                            dates = []
                            if t.start_date:
                                dates.append(f"Start: {t.start_date}")
                            if t.completion_date:
                                dates.append(f"Completion: {t.completion_date}")
                            print(f"    {' | '.join(dates)}")
                    print()
                
                if response.sites:
                    print("🏥 Sites:")
                    for s in response.sites:
                        location = ", ".join(filter(None, [s.city, s.country]))
                        print(f"  • {s.facility} ({location}) - {s.nct_id}")
                    print()
                
                if response.criteria:
                    print("✅ Inclusion Criteria:")
                    for c in response.criteria.inclusion:
                        print(f"  • {c}")
                    print("\n❌ Exclusion Criteria:")
                    for c in response.criteria.exclusion:
                        print(f"  • {c}")
                    print()
                
                if response.sources:
                    print("📚 Sources:")
                    for src in response.sources:
                        print(f"  • {src}")
            
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            logger.log_error(e)
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
