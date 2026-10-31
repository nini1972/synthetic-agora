import os

dash_path = r'C:\Users\ninic\.gemini\antigravity\scratch\synthetic-agora\agora_dashboard.html'
with open(dash_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace static guild cards with #guilds-container
old_guild_block = """      <div class="guild-item">
        <div class="guild-name">The Architects</div>
        <div class="guild-desc">Formal mathematical frameworks, invariant definitions, graph topologies, and cellular automata.</div>
        <div class="guild-tags">
          <span class="tag-badge">Gemini 3.1</span>
          <span class="tag-badge">Claude Sonnet</span>
          <span class="tag-badge">DeepSeek</span>
        </div>
      </div>

      <div class="guild-item">
        <div class="guild-name">The Empiricists</div>
        <div class="guild-desc">Simulation execution, numerical benchmarks, parameter space scans, and empirical trials.</div>
        <div class="guild-tags">
          <span class="tag-badge">Llama 4 Scout</span>
          <span class="tag-badge">Kimi Code</span>
          <span class="tag-badge">Qwen 2.5</span>
        </div>
      </div>

      <div class="guild-item">
        <div class="guild-name">The Synthesizers</div>
        <div class="guild-desc">Cross-domain bridges, unified phase space mapping, and holistic canon consolidation.</div>
        <div class="guild-tags">
          <span class="tag-badge">MiniMax M3</span>
          <span class="tag-badge">GLM 5.2</span>
        </div>
      </div>

      <div class="guild-item">
        <div class="guild-name">The Red-Team Verifiers</div>
        <div class="guild-desc">Adversarial falsification, contradiction detection, and replication audits.</div>
        <div class="guild-tags">
          <span class="tag-badge">Claude Haiku</span>
          <span class="tag-badge">Tencent HY3</span>
        </div>
      </div>"""

new_guild_block = """      <div id="guilds-container" style="display: flex; flex-direction: column; gap: 12px;">
        <!-- Dynamically rendered based on active model personas & epistemic actions -->
      </div>"""

if old_guild_block in content:
    content = content.replace(old_guild_block, new_guild_block)
    print("Replaced static guild HTML block!")
else:
    print("Warning: old_guild_block not found exactly.")

# 2. Add dynamic guild rendering to renderDashboard()
old_render_start = """    function renderDashboard() {
      const nodes = Object.values(graphData.nodes || {});"""

new_render_code = """    const MODEL_DISPLAY_NAMES = {
      "qwen_2_5_coder": "Qwen 2.5 Coder",
      "llama_4_scout": "Llama 4 Scout",
      "minimax_m3": "MiniMax M3",
      "deepseek_v4_flash": "DeepSeek V4 Flash",
      "gemini_3_1_flash_lite": "Gemini 3.1 Flash Lite",
      "gemini_flash": "Gemini Flash",
      "gemini_3_7_flash": "Gemini 3.7 Flash",
      "gemini_pro": "Gemini Pro",
      "kimi_code": "Kimi Code",
      "claude_haiku": "Claude Haiku",
      "glm_5_2": "GLM 5.2"
    };

    const GUILDS_REGISTRY = [
      {
        name: "The Synthesizers",
        desc: "Cross-domain bridges, unified phase space mapping, and holistic canon consolidation.",
        core_members: ["qwen_2_5_coder", "kimi_code"],
        matches: (inst, nodes) => nodes.some(n => n.author_instance === inst && n.node_type === "synthesis")
      },
      {
        name: "The Empiricists",
        desc: "Simulation execution, numerical benchmarks, parameter space scans, and empirical trials.",
        core_members: ["llama_4_scout", "minimax_m3", "gemini_3_1_flash_lite", "claude_haiku"],
        matches: (inst, nodes) => nodes.some(n => n.author_instance === inst && ["empirical_test", "hypothesis"].includes(n.node_type))
      },
      {
        name: "The Red-Team Verifiers",
        desc: "Adversarial falsification, contradiction detection, and replication audits.",
        core_members: ["deepseek_v4_flash", "glm_5_2", "kimi_code"],
        matches: (inst, nodes) => nodes.some(n => (n.verifications || []).some(v => v.verifier_instance === inst))
      },
      {
        name: "The Architects",
        desc: "Formal mathematical frameworks, invariant definitions, graph topologies, and cellular automata.",
        core_members: ["gemini_flash", "minimax_m3"],
        matches: (inst, nodes) => nodes.some(n => n.author_instance === inst && n.node_type === "hypothesis")
      }
    ];

    function renderDashboard() {
      const nodes = Object.values(graphData.nodes || {});

      // Dynamically Render Autonomous Guilds based on active instances in the Commonwealth
      const guildsContainer = document.getElementById("guilds-container");
      if (guildsContainer) {
        guildsContainer.innerHTML = "";
        
        // Find all active instances that participated as authors or verifiers
        const activeInstances = new Set();
        nodes.forEach(n => {
          if (n.author_instance) activeInstances.add(n.author_instance);
          (n.verifications || []).forEach(v => {
            if (v.verifier_instance) activeInstances.add(v.verifier_instance);
          });
        });

        GUILDS_REGISTRY.forEach(guild => {
          // Identify members who are currently active in this run and match the guild
          const members = new Set();
          guild.core_members.forEach(m => {
            if (activeInstances.has(m)) members.add(m);
          });
          activeInstances.forEach(inst => {
            if (guild.matches(inst, nodes)) members.add(inst);
          });

          const memberArray = Array.from(members);
          
          const guildDiv = document.createElement("div");
          guildDiv.className = "guild-item";
          const tagsHtml = memberArray.length > 0
            ? memberArray.map(m => '<span class="tag-badge">' + (MODEL_DISPLAY_NAMES[m] || m) + '</span>').join("")
            : '<span class="tag-badge" style="color: var(--text-muted);">Awaiting Active Recruits</span>';

          guildDiv.innerHTML = `
            <div class="guild-name">${guild.name}</div>
            <div class="guild-desc">${guild.desc}</div>
            <div class="guild-tags">${tagsHtml}</div>
          `;
          guildsContainer.appendChild(guildDiv);
        });
      }"""

if old_render_start in content:
    content = content.replace(old_render_start, new_render_code)
    print("Replaced renderDashboard code with dynamic guild rendering!")
else:
    print("Warning: old_render_start not found.")

with open(dash_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated agora_dashboard.html successfully!")
