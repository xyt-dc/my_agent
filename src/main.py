import asyncio
from dotenv import load_dotenv
load_dotenv()

from llm import get_llm
from agent import Agent

async def spinner(text="思考中"):
    chars = [ "⠋" , "⠙" , "⠹" , "⠸" , "⠼" , "⠴" , "⠦" , "⠧" , "⠇" , "⠏" ]
    while True :
        print ( f"\r {text} {chars[i % len (chars)]} " , end= "" , flush= True )
        i += 1 
        await asyncio.sleep( 0.1 )

async def main():
    agent = Agent(get_llm())
    print('欢迎来到我的agent，请在下方输入您的问题，输入exit、q退出')

    while True:
        user_input = input("输入问题：")

        if user_input == 'exit' or user_input == 'q':
            break
        if not user_input.strip():
            continue
        
        spinner_task = asyncio.create_task(spinner("思考中"))
        first_chunk = True
        print("回复：", end= "" , flush= True )
        async for chunk in agent.ask(user_input): 
            if first_chunk:
                first_chunk = False
                spinner_task.cancel()
                continue
            print (chunk, end= "" , flush= True )
        print("\n")

asyncio.run(main())

