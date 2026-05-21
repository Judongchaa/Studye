# TUI Aesthetic Guide: Sleek, Modern, and Minimal

This guide outlines the design philosophy and technical implementation used to achieve a minimalist, high-density, and aesthetic Look for [Textual](https://textual.textualize.io/) applications, inspired by projects like `bulletty`.

## 1. Design Philosophy

*   **Remove the "Chrome":** Eliminate heavy borders, panels, and standard TUI "windows." Use whitespace and subtle vertical/horizontal lines (like `panel` or `vert` borders with low opacity) for separation.
*   **High-Signal Highlights:** Avoid blocky background highlights for focus. Instead, use **bold text** and **color shifts** (vibrant accents) to indicate the active element.
*   **Muted Neutrality:** Use a dark, neutral background (e.g., Dracula or Nord themes) and dim non-essential information (like dates or "read" status) using low opacity.
*   **Information Density:** Minimize vertical padding. Aim for single-line entries in lists to allow the user to scan more content at once.

## 2. Color Palette (Dracula-Inspired)

| Variable | Color Hex | Purpose |
| :--- | :--- | :--- |
| `$bg` | `#282a36` | Main screen background |
| `$accent` | `#6272a4` | Primary brand/folder color |
| `$text` | `#f8f8f2` | Active/Unread text |
| `$text-muted` | `#6272a4` | Metadata/Read text |
| `$selection-bg` | `#44475a` | Subtle background highlights |
| **Focus Green** | `#50fa7b` | Keyboard focus (Vibrant) |
| **Focus Pink** | `#ff79c6` | Special indicators (Vibrant) |

## 3. CSS Implementation Strategy

### A. The Clean Container
Remove standard widget styling to create a seamless background.

```css
Screen {
    background: #282a36;
}

Header, Footer {
    background: transparent;
    color: #6272a4;
}

/* Use a single vertical line for pane separation instead of a full border */
#content-area {
    border-left: panel #44475a;
    padding-left: 2;
}
```

### B. High-Density List Items
Use a flat structure to keep items compact.

```css
ListItem {
    layout: horizontal;
    height: 1;
    padding: 0 1;
    background: transparent;
}
```

### C. Keyboard Focus (The Arrow Selection)
This is the most critical part of the aesthetic. Target the `--highlight` class applied by `ListView` and use `!important` to ensure the color shift wins over "read/unread" states.

```css
/* Targeting the active item in a ListView */
ListView > ListItem.--highlight {
    background: transparent; /* No blocky background */
}

ListView > ListItem.--highlight #title {
    text-style: bold;
    color: #50fa7b !important; /* Vibrant color shift */
}

ListView > ListItem.--highlight #indicator-dot {
    text-style: bold;
    color: #ff79c6 !important; /* Accent color shift */
}
```

### D. Meaningful States (Read vs. Unread)
Use opacity and desaturation to differentiate between content states without adding visual clutter.

```css
.unread {
    color: #f8f8f2;
}

.read {
    color: #6272a4;
    opacity: 0.5; /* Muted appearance */
}
```

## 4. Key Widget Tips

*   **DirectoryTree:** Hide file extensions and icons if they aren't critical.
    ```css
    DirectoryTree > .directory-tree--extension { display: none; }
    DirectoryTree > .directory-tree--file { display: none; }
    ```
*   **Modals:** Use a semi-transparent background overlay and a borderless dialog box to keep the focus centered.
    ```css
    ModalScreen {
        background: rgba(0, 0, 0, 0.5);
        align: center middle;
    }
    ```

## 5. Summary for LLM Customization
When asking an LLM to apply this style to a new app, provide the following instruction:
> "Apply a minimalist TUI aesthetic. Remove all widget borders and use a single vertical line for layout separation. Implement a Dracula-inspired color palette. For keyboard focus in lists, do not use background highlights; instead, make the focused text bold and shift its color to vibrant green (#50fa7b). Ensure metadata and 'read' states are muted with 50% opacity."
