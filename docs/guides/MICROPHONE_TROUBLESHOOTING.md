# Microphone Troubleshooting Guide

## Problem: Robot Not Hearing Your Voice

If the robot is not responding when you speak, follow these steps:

### Quick Test

Run the microphone test script:
```bash
python test_microphone.py
```

This will diagnose your microphone and show you what's wrong.

---

## Common Issues & Solutions

### 1. Microphone Not Detected

**Symptoms:**
- No response when speaking
- "No speech detected" messages

**Solutions:**
- Check if microphone is physically connected
- Make sure microphone is not muted (check system tray icon)
- Verify microphone is selected as default input device in Windows Sound Settings
- Try unplugging and reconnecting the microphone

### 2. Microphone Volume Too Low

**Symptoms:**
- Robot sometimes hears you, sometimes doesn't
- Works only when speaking very loudly

**Solutions:**
- Open Windows Sound Settings → Input → Microphone
- Increase microphone volume to 80-100%
- Enable "Microphone Boost" if available
- Speak closer to the microphone (6-12 inches away)

### 3. Wrong Microphone Selected

**Symptoms:**
- Multiple microphones available
- Robot not responding

**Solutions:**
- Run `test_microphone.py` to see all available microphones
- Select the correct microphone when prompted
- Set the correct microphone as default in Windows Sound Settings

### 4. Background Noise Too High

**Symptoms:**
- Robot hears noise but not your voice
- "Could not understand audio" messages

**Solutions:**
- Move to a quieter location
- Reduce background music/TV volume
- Close windows to reduce outside noise
- Use a directional microphone instead of omnidirectional
- The robot auto-calibrates for ambient noise, so wait 2-3 seconds after it says "Listening"

### 5. Internet Connection Issues

**Symptoms:**
- "Speech recognition service error" messages
- Works sometimes, fails other times

**Solutions:**
- Check your internet connection
- Google Speech Recognition requires internet
- Try restarting your router
- Check if firewall is blocking Python

### 6. Microphone Permissions

**Symptoms:**
- Error messages about microphone access
- Robot can't initialize microphone

**Solutions:**
- Windows Settings → Privacy → Microphone
- Enable "Allow apps to access your microphone"
- Enable for Python specifically if listed

---

## Testing Steps

### Step 1: System Test
1. Open Windows Sound Settings
2. Go to Input → Test your microphone
3. Speak and watch the blue bar move
4. If bar doesn't move, microphone is not working

### Step 2: Python Test
1. Run: `python test_microphone.py`
2. Follow the prompts
3. Speak clearly when prompted
4. Check if your speech is recognized

### Step 3: Robot Test
1. Start the robot: `python main_robot.py`
2. Wait for "Listening..." message
3. Speak clearly: "Hello robot"
4. Watch for response

---

## Optimal Microphone Settings

### Recommended Settings:
- **Volume:** 80-100%
- **Boost:** +10 to +20 dB (if available)
- **Sample Rate:** 44100 Hz or 48000 Hz
- **Bit Depth:** 16-bit
- **Channels:** Mono or Stereo (both work)

### Speaking Tips:
- Speak clearly and at normal pace
- Don't whisper or shout
- Wait for "SPEAK NOW!" message
- Speak within 6-12 inches of microphone
- Avoid speaking too fast
- Pause briefly between sentences

---

## Advanced Troubleshooting

### Check Microphone in Device Manager:
1. Open Device Manager (Win + X → Device Manager)
2. Expand "Audio inputs and outputs"
3. Look for your microphone
4. If yellow warning icon, update driver
5. Right-click → Update driver

### Test with Other Apps:
- Try recording in Windows Voice Recorder
- Test in Discord or Zoom
- If it works there but not in robot, contact support

### Reinstall Audio Drivers:
1. Device Manager → Audio inputs
2. Right-click microphone → Uninstall device
3. Restart computer
4. Windows will reinstall drivers

---

## Still Not Working?

### Check Python Dependencies:
```bash
pip install --upgrade SpeechRecognition pyaudio
```

### Check Microphone List:
```python
import speech_recognition as sr
print(sr.Microphone.list_microphone_names())
```

### Enable Debug Mode:
Edit `voice/stt.py` and the robot will show detailed microphone information.

---

## Energy Threshold Adjustment

The robot uses an "energy threshold" to detect speech. If it's too high, it won't hear you. If too low, it picks up noise.

**Current default:** 300

**To adjust manually:**
1. Open `voice/stt.py`
2. Find: `self.recognizer.energy_threshold = 300`
3. Try lower values (200-250) for quiet environments
4. Try higher values (400-500) for noisy environments

---

## Contact Support

If none of these solutions work:
1. Run `test_microphone.py` and save the output
2. Note your microphone model
3. Note your Windows version
4. Describe exactly what happens when you speak
5. Report the issue with all this information
