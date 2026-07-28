# Signal Shield — Technical Overview for the Team

This document explains how Signal Shield works at every layer. No code background needed. By the end you should be able to explain the product to anyone and understand why we're building what we're building.

---

## Part 1: The Problem

AI voice cloning tools can take a short clip of someone speaking and generate new speech that sounds like them. Some of these tools are free and take less than 30 seconds of audio.

**Our product:** You upload a voice recording, we process it, and you download a version that sounds identical to you but is poisoned for cloning tools. If someone tries to clone your voice from the protected file, the result is degraded or unusable.

---

## Part 2: How Digital Audio Works

Before we can explain the protection, you need to know what audio actually is inside a computer.

### Audio is just a list of numbers

A WAV file is a long list of numbers. Each number represents the position of a speaker cone at a single instant — pushed out (positive number) or pulled in (negative number). There are 22,050 of these numbers per second in our system.

```
  What a speaker does:              What a WAV file stores:

     pushed out (+)                 [ 0.0,  0.3,  0.5,  0.3,
        ▲                            0.0, -0.3, -0.5, -0.3,
        │  ●                          0.0,  0.3,  0.5,  0.3,
        │     ●                       0.0, -0.3, -0.5, -0.3,
  rest ─●────────●──── time           ... 22,050 numbers per second ]
        │           ●
        │              ●
        ▼
     pulled in (-)
```

Play those numbers back fast enough through a speaker and you hear sound. That's it.

### Two ways to look at the same audio

There are two equally valid ways to describe any sound:

**View 1 — Time domain:** "What is the speaker doing at each moment?"
This is the list of numbers above. It's what you see in a waveform editor.

**View 2 — Frequency domain:** "Which frequencies are present and how loud are they?"
This is what you see on an equalizer — bass on the left, treble on the right.

```
  TIME DOMAIN                        FREQUENCY DOMAIN
  (waveform)                         (equalizer)

  ▲ amplitude                        ▲ loudness
  │                                  │
  │ /\  /\  /\  /\  /\               │ █
  │/  \/  \/  \/  \/  \              │ █ █
  │                                  │ █ █
  └──────────────────► time          └──────────────────► frequency
                                      low            high
  "What's happening each moment"     "Which frequencies are playing"
```

These two views contain exactly the same information — you can convert back and forth without losing anything. The math that converts between them is called the **Fourier Transform**.

---

## Part 3: Magnitude and Phase

Here's the key insight that makes our product possible.

In the frequency domain, each frequency has two properties:

### Magnitude — "how loud is this frequency?"

This is what your ears primarily care about. A voice sounds like a specific person because of the unique pattern of loud and quiet frequencies (called the vocal timbre). Change the magnitudes and the voice sounds different.

### Phase — "where in the wave cycle is this frequency?"

Imagine two identical tuning forks. Both vibrate at the same frequency at the same volume. But if one starts at the peak of its vibration while the other starts at the bottom, they're out of phase. Humans can barely tell the difference, especially for high frequencies.

```
  Same magnitude, different phase:

  Fork A (phase = 0°):            Fork B (phase = 180°):

       /\      /\      /\               /\      /\
      /  \    /  \    /  \         \  /    \  /    \  /
  ───/    \──/    \──/    \───   ───\/      \/      \/───
           \/      \/

  Sound the same to humans.
  Look VERY different to AI models.
```

**The key fact:** Human ears are insensitive to phase above about 10,000 Hz. But AI cloning models use phase data as part of their input. This gap between human perception and machine perception is what we exploit.

---

## Part 4: How Signal Shield Works (Current Version)

### The three-step process

```
  Your audio file
       │
       ▼
  ┌─────────┐     Convert from time view to frequency view.
  │  STFT   │     Now we can see magnitude and phase separately
  └────┬────┘     for every frequency at every moment.
       │
       ▼
  ┌─────────┐     Flip the phase for every frequency above 10,000 Hz.
  │  Phase  │     Magnitude (loudness) is NEVER touched.
  │  Flip   │     Think of it as: rearranging the furniture in a room
  └────┬────┘     that nobody can see into.
       │
       ▼
  ┌─────────┐     Convert back from frequency view to time view.
  │ iSTFT   │     Result: a normal audio file you can play anywhere.
  └────┬────┘
       │
       ▼
  Protected audio file
```

### Why this preserves quality

We never touch magnitude. Magnitude is what determines how a voice sounds to human ears — the pitch, the tone, the clarity. Since we only modify phase (which humans can't perceive above 10kHz), the protected audio sounds identical to the original.

### Why this disrupts cloning

Cloning models process the full frequency data — both magnitude and phase — when they analyze a voice sample. By scrambling the phase above 10kHz, we're feeding the model corrupted data. It's like handing someone a jigsaw puzzle where half the pieces have been flipped upside down — they can see the picture on each piece, but they can't assemble it correctly.

---

## Part 5: The Limitation

**Here's the honest problem:** Some modern cloning models don't use phase at all. They convert audio into a representation called a "mel spectrogram" that only captures magnitude. For those models, our phase flip does nothing — they never look at the data we changed.

```
  Model uses full spectrum:              Model uses mel spectrogram only:

  Reads magnitude ✓                      Reads magnitude ✓
  Reads phase ✓                          Ignores phase entirely
         │                                        │
  Phase is scrambled → MODEL CONFUSED    Phase is scrambled → MODEL DOESN'T CARE
         │                                        │
  Protection: WORKS ✓                    Protection: DOES NOT WORK ✗
```

This is why we need the adversarial optimization upgrade.

---

## Part 6: The Upgrade — Adversarial Optimization

Instead of hoping our fixed transformation breaks the cloning model, we directly test against it and design our perturbation to maximize damage.

### The concept

Imagine you're trying to sabotage an exam for a specific student. The static approach (current) is like scrambling random questions — maybe it helps, maybe the student doesn't even use those questions. The adversarial approach is like reading the student's study notes, finding exactly what they rely on, and specifically corrupting those parts.

### How it works

```
  Step 1: Start with the original audio and zero perturbation (silence)

  Original audio:  [0.3, 0.5, 0.2, -0.1, ...]
  Perturbation:    [0.0, 0.0, 0.0,  0.0, ...]   ← starts as silence
  Combined:        [0.3, 0.5, 0.2, -0.1, ...]   ← same as original


  Step 2: Feed the combined audio to the cloning model

  Combined audio ──► Cloning Model ──► Voice fingerprint
                                             │
                                      Compare to original
                                      voice fingerprint
                                             │
                                             ▼
                                     "How similar are they?"
                                     (This is the "loss")


  Step 3: Ask "how should I change the perturbation to make the
  model MORE wrong?"

  This is done with calculus (gradients). The model is made of math,
  so we can trace backward through it to find the answer:
  "If I make sample #47 a tiny bit louder and sample #203 a tiny
  bit quieter, the model gets more confused."


  Step 4: Update the perturbation

  Perturbation:    [0.0, 0.0, ..., +0.001, ..., -0.002, ...]
                                     ▲               ▲
                              sample #47        sample #203


  Step 5: Make sure the perturbation is still inaudible

  If any value in the perturbation is too large (would be audible),
  clip it back down.


  Repeat steps 2-5 many times (typically 50-200 rounds).


  Final result:

  Original audio:  [0.3,    0.5,    0.2,    -0.1,   ...]
  Perturbation:    [0.002, -0.001,  0.003,  -0.001, ...]  ← tiny, inaudible
  Protected audio: [0.302,  0.499,  0.203,  -0.101, ...]  ← sounds the same but model can't clone it              
                                                              
```

### Why this is better

| | Static (current) | Adversarial (planned) |
|---|---|---|
| **How it works** | Same fixed transformation for every file | Custom perturbation per file, optimized against a real model |
| **Speed** | Fast (single pass) | Slower (50-200 optimization rounds) |
| **Effectiveness** | Only works if the model uses the data we changed | Directly tested and optimized against the target model |
| **Adaptability** | None — same approach regardless of threat | Can target specific cloning models |

### What stays the same

The adversarial upgrade only changes the **processing engine** inside the backend. Everything else remains identical:

```
                           ┌───────────────────────────┐
  Browser ──► Frontend ──► │  Backend API endpoint     │ ──► Browser
                           │                           │
                           │  Currently:               │
                           │  ┌──────────────────────┐ │
                           │  │ Static phase flip    │ │
                           │  └──────────────────────┘ │
                           │                           │
                           │  After upgrade:           │
                           │  ┌──────────────────────┐ │
                           │  │ Adversarial optimizer│ │
                           │  └──────────────────────┘ │
                           │                           │
                           │  Same input, same output  │
                           │  Same API, same frontend  │
                           └───────────────────────────┘
```

The user still uploads a file and gets a protected file back. The frontend doesn't change. The API endpoint doesn't change. Only the engine under the hood changes.

---

## Glossary

| Term | Plain English |
|------|--------------|
| **STFT** | Math that converts audio from "what's happening each moment" to "which frequencies are present." Reversible. |
| **iSTFT** | The reverse of STFT. Converts frequency data back to normal audio. |
| **Magnitude** | How loud a frequency is. What humans hear. We never change this. |
| **Phase** | The timing offset of a frequency's wave. Mostly inaudible to humans. We manipulate this. |
| **Mel spectrogram** | A simplified frequency representation that only captures magnitude. Some cloning models use this, which is why static phase flipping doesn't always work. |
| **Perturbation** | A tiny noise pattern added to audio. If done right, it's inaudible but disrupts AI models. |
| **Gradient** | The mathematical answer to "which direction should I change the perturbation to make the model more confused?" |
| **Adversarial optimization** | The process of iteratively adjusting a perturbation to maximally break a specific AI model. |
| **Speaker embedding** | A list of numbers that a cloning model produces to capture "what this voice sounds like." Our goal is to make this output wrong. |
