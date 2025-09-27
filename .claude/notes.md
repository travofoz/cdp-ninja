# CDP Ninja Agent Research Notes

## Current Agent Analysis

The current CDP Ninja agent (`/agent/cdp-ninja.md`) has several issues:

**Problems identified:**
- Very minimal guidance - just lists API endpoints
- No strategic thinking about when/how to use tools efficiently
- No guardrails on tool usage (user complains it "calls 96 tools")
- No focus on specific use cases (user wants "logs and screenshot analysis")
- No guidance on prioritization or stopping conditions
- Just a raw list of endpoints without workflow guidance

**Current agent approach:**
- Basic name/description/tools header
- Long list of API endpoints with JSON examples
- Ends with "No input validation. No sanitization. Raw pass-through to Chrome."
- Relies on WebFetch tool to call CDP bridge

## Research Goals

Need to find patterns for:
1. **Focus and efficiency** - How to avoid calling too many tools
2. **Task prioritization** - When to stop, what's essential vs nice-to-have
3. **Workflow guidance** - Step-by-step approaches for common scenarios
4. **Guardrails** - How to prevent agent from going down rabbit holes
5. **Use case specific guidance** - Different approaches for debugging vs automation

---

## Resource Research

### 1. wshobson/agents Repository

**Key Insights:**
- **Domain Specialization**: 83 specialized agents, each with clear domain focus (Architecture, Programming Languages, Infrastructure, etc.)
- **Model Selection Strategy**:
  - Haiku for "quick, focused tasks"
  - Sonnet for "standard development tasks"
  - Opus for "complex reasoning and critical analysis"
- **Scoped Capabilities**: Each agent has 8-12 specific capability areas, not generic catch-all
- **Tight Descriptions**: e.g., "Web3 apps, smart contracts, DeFi protocols" - very specific, not vague
- **Action-Oriented Language**: Focus on what the agent DOES, not what it knows

**Anti-Patterns Identified:**
- Generic agents that try to do everything
- Unclear scope leading to unfocused behavior
- Wrong model selection for task complexity

**Relevant for CDP Ninja:**
- Need to specialize the agent for specific browser debugging scenarios
- Should have clear stopping conditions and scope boundaries
- Consider different agent variants for different use cases (quick debug vs deep analysis)

### 2. Anthropic Engineering: Writing Tools for Agents

**Critical Insights:**
- **"More tools don't always lead to better outcomes"** - This directly addresses the "96 tools" problem!
- **Context Limitations**: Agents have limited context vs computer memory - need to be surgical
- **Consolidation Strategy**: Replace multiple small tools with focused, high-impact workflows
- **Skip to Relevance**: Tools should "skip to the relevant page first" instead of brute-force searching

**Tool Design Principles:**
- Implement pagination, filtering, and truncation to limit response size
- Consolidate multi-step operations into single, focused tools
- Example from post: Replace `list_users`, `list_events`, `create_event` with single `schedule_event`
- Use clear, distinct tool names reflecting natural task subdivisions
- Allow agents to control response verbosity via parameters

**Anti-Patterns Identified:**
- Tools that return massive, irrelevant datasets
- Brute-force searching instead of targeted queries
- Multiple small tools when one consolidated tool would work better

**Debugging Agent Specifics:**
- Use evaluation tasks that mirror real-world complexity
- Collect metrics: tool call frequency, runtime, errors
- Analyze agent reasoning via "interleaved thinking"
- Continuously refine tool descriptions based on evaluation results

**For CDP Ninja Agent:**
- Need consolidated workflows like "quick_debug_analysis" instead of separate screenshot + logs + network calls
- Should have verbosity controls (brief vs detailed analysis)
- Must have clear stopping conditions to prevent tool spam

### 3. Claude Code Sub-Agents Documentation

**Structure Guidelines:**
- Agents need "specific purpose and expertise area"
- Clear description of WHEN the agent should be used
- Detailed system prompt defining "role, capabilities, and approach"
- Use "use PROACTIVELY" to encourage targeted behavior

**Tool Management:**
- Grant only necessary tools for the agent's purpose
- Can inherit all tools or specify limited set
- Recommendation: Use `/agents` command to modify tool access

**Scope Best Practices:**
- "Design focused subagents" with "single, clear responsibilities"
- Avoid agents that try to do everything
- Narrow, well-defined objectives prevent unfocused behavior

**Specialized Agent Patterns:**
- Debugging agents: Include "root cause analysis" process
- Code review agents: Structured checklist approach
- Data analysis agents: Emphasize efficiency and clear documentation

**Key Quote:** "Start with Claude-generated agents... a solid foundation that you can customize to your specific needs."

**For CDP Ninja:**
- Current agent is too broad - needs specific debugging scenarios
- Should limit tool access to prevent "96 tools" problem
- Need clear "when to use" guidelines for different situations
- Consider root cause analysis workflow for debugging scenarios

### 4. Anthropic Claude Cookbooks

**Source:** https://github.com/anthropics/claude-cookbooks

**Key Patterns:**
- **Controlled Tool Integration**: Customer service agent example shows bounded tool usage
- **Moderation Filters**: Building moderation filters to prevent off-scope responses
- **Sub-Agent Strategies**: Using Haiku as sub-agent with Opus - strategic model selection
- **JSON Mode**: Structured outputs prevent meandering conversations
- **Automated Evaluations**: Systematic assessment to refine tool usage

**For CDP Ninja:**
- Need moderation to prevent going off-track
- Consider sub-agent approach for different complexity levels
- Structured outputs for consistent debugging reports

### 5. Anthropic 2025 Agent Design Best Practices

**Sources:**
- https://www.anthropic.com/engineering/building-effective-agents
- https://www.anthropic.com/engineering/writing-tools-for-agents
- https://github.com/orgs/anthropics/repositories

**Core Principles:**
- **Simplicity & Transparency**: Show agent's planning steps explicitly
- **Agent vs Workflow**: Agents dynamically direct their processes vs predefined code paths
- **Tool Philosophy**: "Effective tools are intentionally and clearly defined, use agent context judiciously"

**Design Patterns:**
- **Prompt Chaining**: Break complex tasks into sequential steps
- **Routing**: Classify input and direct to specialized agents
- **Parallelization**: Sectioning (independent subtasks) and Voting (diverse outputs)

**Tool Development:**
- Start with quick prototype, then comprehensive evaluation
- Let agents analyze results and improve tools
- Tools should be combinable in diverse workflows

**Multi-Agent Systems:**
- Use 15× more tokens than chat but excel at valuable, complex tasks
- Good for: heavy parallelization, large context windows, numerous complex tools

**Safety & Oversight:**
- Balance autonomy with human oversight
- Transparency in problem-solving processes
- Human control over high-stakes decisions

### 6. Nine Schools Concept 🥷

**Future Consideration:** Split CDP Ninja into specialized agents based on ninjutsu schools:
- Each "school" handles specific browser debugging scenarios
- Different philosophies and approaches per school
- More focused and powerful than one generic agent

---

## Synthesis & Recommendations

### The Core Problem
Current CDP Ninja agent is a "sperg" that "calls 96 tools" because:
1. **No boundaries** - Generic agent tries to do everything
2. **No stopping conditions** - No guidance on when enough is enough
3. **Tool spam** - Multiple small calls instead of consolidated workflows
4. **No focus** - User wants "logs and screenshot analysis" but agent goes everywhere

### Key Solutions from Research

**1. Specialization Over Generalization**
- Current: One generic "cdp-ninja" agent
- Better: Multiple focused agents for specific scenarios
- Best: "Nine Schools" - specialized agents with clear philosophies

**2. Consolidated Workflows**
- Current: Separate calls for screenshot + logs + network + DOM queries
- Better: Single "quick_debug_analysis" workflow
- Best: Pre-built debugging patterns that get right info efficiently

**3. Clear Boundaries and Stopping Conditions**
- Current: No guidance on scope or when to stop
- Better: Explicit "when to use" guidelines and tool limits
- Best: Built-in moderation and focus mechanisms

**4. Strategic Tool Design**
- Current: Raw API endpoint list with no strategy
- Better: Consolidated tools that "skip to relevant" instead of brute force
- Best: Context-aware tools with verbosity controls

### Immediate Recommendations

**Phase 1: Fix Current Agent (Quick Win)**
1. **Add Scope Boundaries**: Clear "when to use" section
2. **Consolidate Common Workflows**: Create "quick_debug", "deep_analysis", "screenshot_review" patterns
3. **Add Stopping Conditions**: Built-in limits and focus guidelines
4. **Verbosity Controls**: Brief vs detailed analysis modes

**Phase 2: Nine Schools Architecture (Future)**

**Source:** https://en.wikipedia.org/wiki/Bujinkan

1. **Togakure Ryū** (Hidden Door School) - *Foundation & Spiritual*
   - Core debugging philosophy and spiritual discipline
   - The "18 skills" of browser debugging fundamentals
   - Overall coordination and tactical approach

2. **Gyokushin Ryū** (Jewel Heart School) - *Espionage & Intelligence*
   - Network monitoring, traffic analysis, data extraction
   - Stealthy information gathering, API reconnaissance
   - Specialized in "sacrifice techniques" - controlled failures to gain intel

3. **Kumogakure Ryū** (Cloud Hiding School) - *Background Operations*
   - Silent background monitoring, async operations
   - Performance profiling, memory analysis
   - Hidden from view but always watching

4. **Kotō Ryū** (Tiger Knock Down School) - *Structural Breaking*
   - DOM manipulation, element destruction, structural testing
   - "Attacking the skeletal structure" - breaking page frameworks
   - Aggressive stress testing, intentional breaking

5. **Gyokko Ryū** (Jewel Tiger School) - *Precision Targeting*
   - Muscle memory and weak point analysis
   - Precise element targeting, CSS selector mastery
   - Form validation, input field manipulation

6. **Kuki Shinden Ryū** (Nine Demons Divine Transmission) - *Weapons & Tools*
   - Advanced tool mastery, weapon-focused approach
   - JavaScript injection, console manipulation
   - Modern and traditional debugging weapons

7. **Shinden Fudō Ryū** (Divine Immovable School) - *Direct Combat*
   - Direct confrontation with bugs and errors
   - Strikes, kicks, blocks - immediate action debugging
   - Console error fighting, exception handling

8. **Takagi Yōshin Ryū** (High Tree Raised Heart) - *Relaxed Method*
   - Gentle debugging approach, user experience focus
   - Throwing, grappling with UI issues
   - Accessibility testing, smooth interactions

9. **Gikan Ryū** (Righteous School) - *Complementary Breaking*
   - Security testing, penetration testing
   - Bone manipulation - deep structural analysis
   - Complementary to Kotō Ryū's approach

Each school would have:
- **Specific philosophy** matching their martial art approach
- **Specialized tools** relevant to their domain
- **Built-in stopping conditions** based on their discipline
- **Consolidated workflows** for their specialty
- **Clear boundaries** on when to engage vs defer to other schools

### Ninja Philosophy Integration

**See ninja-background.md for complete historical research and lore**

**Key Applications for Agent Design:**
- **Feel-Based Debugging**: Intuitive pattern recognition over rigid procedures (Hatsumi)
- **Multi-Style Mastery**: Multiple debugging approaches, not just one (Takamatsu)
- **Bridge Traditional + Modern**: Classic debugging with CDP techniques (Fujita)
- **Strategic Adaptation**: Change approach based on situation (Musashi)
- **Seven Ways of Authentication**: Different agent modes for different debugging scenarios

### Next Steps
1. Start with Phase 1 improvements to current agent
2. Test and evaluate tool usage patterns
3. Identify natural specialization boundaries
4. Design Nine Schools architecture based on real usage data
5. Apply Fujita's philosophy: balance research/documentation with practical debugging
