# The Absolute Beginner's Guide to Android Claude Controller (ACC)

Welcome! If you're not a programmer or tech expert, you're in the right place. This guide will walk you through setting up and using the Android Claude Controller step by step.

## What is this thing?

Imagine if you could just tell your phone what to do by typing it out in plain English. For example, "Open the calculator and add 20 to 45" or "Open Instagram and tell me what the first post is." 

That's exactly what **Android Claude Controller (ACC)** does. It acts as a bridge between a super-smart AI (like Claude or DeepSeek) and your Android phone. The AI looks at your phone's screen, figures out what buttons to press, and actually taps the screen for you!

## What do you need before starting?

1. **An Android Phone or Tablet** (It won't work on iPhones).
2. **A Computer** (Windows, Mac, or Linux) OR you can do it entirely on your phone using an app called Termux.
3. **A USB Cable** to connect your phone to your computer.
4. **An API Key** (Think of this as a login password that lets the AI think and make decisions. You can load this with a few cents to start).

---

## Step 1: Getting your AI "Brain" (API Keys)

You need to choose which AI brain you want to use. You have two main choices:

*   **Claude:** Very smart, sees the screen perfectly, but costs a little bit of money (a few cents per task).
*   **DeepSeek:** Cheaper (costs less than a penny per task), but sometimes gets confused if the task is too complicated.

**To get a Claude API Key:**
1. Go to [claude.ai's console](https://console.anthropic.com).
2. Create an account.
3. Add a few dollars of credit (e.g., $5).
4. Go to the "API Keys" section and create a new key. It will look like a long password starting with `sk-ant-`. **Copy this and save it somewhere safe.**

**To get a DeepSeek API Key:**
1. Go to [platform.deepseek.com](https://platform.deepseek.com).
2. Create an account.
3. Add a little bit of credit.
4. Go to the API keys page and create a key. It will start with `sk-`. **Save this somewhere safe.**

---

## Step 2: Preparing your Phone (Developer Options)

We need to turn on a special mode on your phone that allows a computer to click buttons on it. It's perfectly safe, but it's hidden by default.

1. On your phone, open the **Settings** app.
2. Scroll all the way down and tap **About Phone**.
3. Look for something called **Build Number** (sometimes hidden under "Software Information").
4. **Tap "Build Number" 7 times fast.** It will ask for your PIN, and then it will say "You are now a developer!"
5. Go back to the main Settings menu. You will now see a new option called **Developer Options** (sometimes this is under "System").
6. Open Developer Options, scroll down, and turn on **USB Debugging**.

---

## Step 3: Installing the Software

You can do this from a computer (easiest) or directly on your phone.

### Option A: From a Linux Computer (Easiest)
1. Plug your phone into your computer using the USB cable.
2. Your phone will pop up a message asking, "Allow USB debugging?" Check the box that says "Always allow from this computer" and tap **Allow**.
3. Open your terminal app.
4. Type this command to install the required Android tools: `sudo apt install android-sdk-platform-tools adb`
5. Download this project by typing: `git clone https://github.com/tai/android-claude-controller`
6. Go into the folder: `cd android-claude-controller`
7. Install the program: `pip install -e .`

### Option B: Directly on your Phone (Using Termux)
If you don't have a computer, you can run this entirely on your Android phone!
1. Download an app called **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/). *(Don't download it from the Google Play Store, that version is broken).*
2. Open Termux and type these commands one by one, pressing Enter after each:
   *   `pkg update && pkg upgrade` (say yes to any prompts)
   *   `pkg install python python-pip android-tools git`
   *   `termux-setup-storage` (this asks for permission to access your files, tap Allow)
   *   `git clone https://github.com/tai/android-claude-controller`
   *   `cd android-claude-controller`
   *   `pip install -e .`

---

## Step 4: Telling the Program Your API Key

Remember that long password (API key) you got in Step 1? You need to tell the program what it is.

In your terminal or Termux, type:

**If you chose Claude:**
```bash
export ANTHROPIC_API_KEY=your-long-key-goes-here
```

**If you chose DeepSeek:**
```bash
export DEEPSEEK_API_KEY=your-long-key-goes-here
```
*(Replace `your-long-key-goes-here` with your actual key, but keep it all on one line with no spaces around the equals sign).*

---

## Step 5: Start Controlling Your Phone!

Now for the fun part. Make sure your phone is plugged in and awake (or if you're using Termux, just make sure the app is open).

First, check if the program can see your phone by typing:
```bash
acc device list
```
If it shows a string of letters and numbers followed by "device", you are good to go!

### Try your first command!

Type this into your terminal:
```bash
acc goal "open the settings app and tell me what my battery percentage is"
```

The AI will now:
1. Look at your phone's screen.
2. Figure out how to open Settings.
3. Find the battery section.
4. Read the percentage.
5. Report back to you!

### Having a Chat

If you want to give multiple commands in a row, use chat mode! Type:
```bash
acc chat
```
You will enter a chat room where you can just type normal sentences, like:
* "Go to the home screen"
* "Open YouTube"
* "Search for cute cat videos"

When you're done, type `/exit` to leave the chat.

---

## Common Issues & Easy Fixes

**Error: "No ADB devices found"**
*   **Fix:** Unplug your phone and plug it back in. Make sure your phone screen is unlocked. Look at your phone to see if there is a prompt asking to "Allow USB debugging" and tap Allow.

**Error: "API Key not set"**
*   **Fix:** You forgot to do Step 4! Run the `export` command again with your API key. Remember, you have to do this every time you open a new terminal window.

**The AI is getting confused or clicking the wrong things**
*   **Fix:** If you are using DeepSeek, try switching to Claude (it's much smarter). If you are already using Claude, try giving it simpler, step-by-step instructions. Instead of "Send a text to Mom saying hi", try "Open the Messages app", wait for it to finish, and then say "Click on the chat with Mom", and then "Type hi and press send."
