#!/usr/bin/env python
from awscrew import AWSCrew

def main():
    # Get user input
    user_input = input("Welcome to the AWS Crew! Please ask your doubt or question: ")
    
    # Create inputs dictionary
    inputs = {
        'topic': user_input  # Some configs might expect 'topic' instead of 'query'
    }
    
    # Initialize and run the crew
    crew_instance = AWSCrew()
    
    try:
        # Try different approaches to access the crew
        if hasattr(crew_instance, 'crew'):
            # If crew is a property
            result = crew_instance.crew.kickoff(inputs=inputs)
        else:
            # If crew needs to be called as a method
            crew_obj = crew_instance.crew()
            result = crew_obj.kickoff(inputs=inputs)
    except AttributeError as e:
        print(f"Error accessing crew: {e}")
        print("Trying alternative approach...")
        
        # Alternative: manually create the crew
        from crewai import Crew, Process
        manual_crew = Crew(
            agents=[
                crew_instance.aws_query_agent(),
                crew_instance.search_agent(), 
                crew_instance.report_agent()
            ],
            tasks=[
                crew_instance.aws_query_task(),
                crew_instance.search_task(),
                crew_instance.report_task()
            ],
            process=Process.sequential,
            verbose=True
        )
        result = manual_crew.kickoff(inputs=inputs)
    
    # Print the result
    print("=" * 50)
    print("AWS Crew Response:")
    print("=" * 50)
    print(result)

if __name__ == "__main__":
    main()