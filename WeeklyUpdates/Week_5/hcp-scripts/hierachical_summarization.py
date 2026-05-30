# ==========================================
# 0. IMPORT THE REQUIRED DEPENDENCIES
# ==========================================
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from pathlib import Path
from collections import defaultdict
import re
import gc
import sys
import os

# ==========================================
# 1. ENVIRONMENT & MODEL SETUP
# ==========================================
model_name = "ibm-granite/granite-34b-code-instruct-8k" 

hf_token = os.environ.get('HF_TOKEN')
if not hf_token:
    print("WARNING: HF_TOKEN not found.")
    sys.exit()

# ==========================================
# X Hardware optimization (Quantization) X ====> NO need for this step here [WHY?!]
# used for a short amount of time as we ran out of memory at the beginning
# ==========================================
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# ==========================================
# 2. LOAD THE TOKENIZER
# ==========================================
print(f"Loading Tokenizer for {model_name}...")
tokenizer = AutoTokenizer.from_pretrained(
    model_name, 
    token=hf_token, 
    trust_remote_code=False 
)

tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "left" 

# ==========================================
# 3. LOAD THE MODEL
# ==========================================
print("Loading Model across 2x A100 GPUs...")
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    token=hf_token,
    trust_remote_code=False,
    # quantization_config=bnb_config, # used for a short amount of time for bug fixing         
    device_map="auto",
    dtype=torch.bfloat16 #  
)

# ==========================================
# 4. PROMPT VARS
# ==========================================

ONE_SHOT_SEMANTIC_EXAMPLE_INPUT = """Please analyze the following source code:
        <source_code>
            import java.util.List;
            import java.util.ArrayList;

            public class EvenNumberFilter {
                public List<Integer> filterEvens(List<Integer> numbers) {
                    List<Integer> result = new ArrayList<>();
                    for (int n : numbers) {
                        if (n % 2 == 0) {
                            result.add(n);
                        }
                    }
                    return result;
                }
            }
        </source_code>"""

ONE_SHOT_DESCRIPTIVE_EXAMPLE_INPUT = """Please create a high-level descriptive summary for the following:
<semantic_summaries>
**Key Functionality:**
Filters a list of integers, returning only the even numbers.
**Core Logic:**
Iterates over each element in the input list and checks divisibility by 2 using the modulo operator. Matching elements are collected into a new list.
**Inputs/Outputs:**
- Input: `List<Integer> numbers` — a list of integers to be filtered
- Output: `List<Integer>` — a new list containing only the even integers from the input
**Dependencies:**
- `java.util.List` — interface for the input and output list types
- `java.util.ArrayList` — concrete list implementation used to collect results
</semantic_summaries>
<descriptive_summaries>
**Title:** predicates — Parity Predicate Utilities

**Summary:**
The predicates subdirectory provides reusable predicate logic for numeric classification. Its primary component is a ParityChecker class that exposes static boolean methods for determining whether an integer is even or odd. It acts as a pure logic layer with no state or I/O, designed to be consumed by higher-level filtering components. All methods are stateless and side-effect free, depending only on primitive arithmetic.
</descriptive_summaries>"""

ONE_SHOT_SEMANTIC_EXAMPLE_OUTPUT = """**Key Functionality:**
Filters a list of integers, returning only the even numbers.

**Core Logic:**
Iterates over each element in the input list and checks divisibility by 2 using the modulo operator. Matching elements are collected into a new list.

**Inputs/Outputs:**
- Input: `List<Integer> numbers` — a list of integers to be filtered
- Output: `List<Integer>` — a new list containing only the even integers from the input

**Dependencies:**
- `java.util.List` — interface for the input and output list types
- `java.util.ArrayList` — concrete list implementation used to collect results"""

ONE_SHOT_DESCRIPTIVE_EXAMPLE_OUTPUT = """**Title:** EvenNumberFilter — Integer Parity Filter Utility

**Summary:**
EvenNumberFilter is a single-responsibility filtering module that isolates even integers from an arbitrary input list. It is composed of two layers: a `predicates` subdirectory that houses the reusable parity logic, and the top-level filter class itself which orchestrates the linear scan and result collection.

The architecture follows a clean separation of concerns — predicate evaluation is delegated entirely to the stateless `ParityChecker` utilities in the `predicates` layer, while EvenNumberFilter owns the iteration and accumulation logic using a standard ArrayList. Data flows in one direction: the input list is passed down to the filter, elements are tested via the predicate layer, and matching values are collected into a new list that is returned to the caller.

There is no shared mutable state anywhere in the module, making it deterministic and safe for concurrent use. Its only external dependencies are the standard Java Collections API, making it a self-contained leaf cluster with minimal coupling to the broader codebase."""

COT_SEMANTIC = """
Before producing your final summary, reason through the code step by step:
1. Read through the code and identify what each class and method does
2. Trace the core logic and any data transformations
3. Identify all inputs, outputs, and return types
4. Note any imported or external dependencies

Then, present your final summary using exactly these four sections:
- Key Functionality
- Core Logic
- Inputs/Outputs
- Dependencies"""

COT_DESCRIPTIVE = """
Before writing the final output, reason through the following steps:

<reasoning>
1. SEMANTIC ANALYSIS: What is the core functionality and logic of this module based on the semantic summaries? What are its inputs, outputs, and key dependencies?
2. SUBDIRECTORY ANALYSIS: What responsibilities do the subdirectories handle based on the descriptive summaries? How do they relate to the top-level module?
3. ARCHITECTURE: How is the module structured? What are the layers, and what does each own?
4. COMPONENT INTERACTION: How does data flow between the top-level module and its subdirectories? Is there shared state? What are the coupling characteristics?
5. SUMMARY SYNTHESIS: Given the above, what is the most accurate title and concise narrative that captures the module's overall behaviour and design?
</reasoning>

Once you have reasoned through each step, produce the final output in this format:
**Title:** <title>
**Summary:** <summary>"""

# ==========================================
# 5. FUNCTIONS USED FOR TASK
# ==========================================

def get_semantic_summary_zero_shot_prompt(file_content):
    return [
        {
            "role": "system",
            "content": "You are a helpful data scientist for software engineering. Your job is to explain the functionality of the provided code by extracting a semantic summary from the file: (Key functionality, Core logic, Inputs/Outputs, and Dependencies)."
        },
        {
            "role": "user",
            "content": f"""Please analyze the following source code:

            <source_code>
                {file_content}
            </source_code>"""
        }
    ]

def get_semantic_summary_one_shot_prompt(file_content):
    return [
        {
            "role": "system",
            "content": "You are a helpful data scientist for software engineering. Your job is to explain the functionality of the provided code by extracting a semantic summary from the file: (Key functionality, Core logic, Inputs/Outputs, and Dependencies)."
        },
        # --- One-shot example ---
        {
            "role": "user",
            "content": ONE_SHOT_SEMANTIC_EXAMPLE_INPUT
        },
        {
            "role": "assistant",
            "content": ONE_SHOT_SEMANTIC_EXAMPLE_OUTPUT
        },
        # --- Actual task ---
        {
            "role": "user",
            "content": f"""Please analyze the following source code:
        <source_code>
            {file_content}
        </source_code>"""
        }
    ]

def get_semantic_summary_zero_shot_chain_of_thought_prompt(file_content):
    return [
        {
            "role": "system",
            "content": "You are a helpful data scientist for software engineering. Your job is to explain the functionality of the provided code by extracting a semantic summary." + COT_SEMANTIC
        },
        {
            "role": "user",
            "content": f"""Please analyze the following source code:
        <source_code>
            {file_content}
        </source_code>

Walk through your reasoning first, then provide the structured summary."""
        }
    ]

def get_semantic_summary_prompt(file_content, prompt_technique):
    match prompt_technique:
        case "zero-shot":
            return get_semantic_summary_zero_shot_prompt(file_content)
        case "one-shot":
            return get_semantic_summary_one_shot_prompt(file_content)
        case "chain-of-thought":
            return get_semantic_summary_zero_shot_chain_of_thought_prompt(file_content)

def get_descriptive_summary_zero_shot_prompt(user_content):
    return [
        {"role": "system", "content": "You are a helpful data scientist for software engineering. Your job is to create a descriptive summary and a title explaining a software module’s overall behaviour, architecture, and how the components interact within the cluster."},
        {"role": "user", "content": user_content}
    ]

def get_descriptive_summary_one_shot_prompt(user_content):
    return [
        {"role": "system", "content": "You are a helpful data scientist for software engineering. Your job is to create a descriptive summary and a title explaining a software module’s overall behaviour, architecture, and how the components interact within the cluster."},
        # --- One-shot example ---
        {
            "role": "user",
            "content": ONE_SHOT_DESCRIPTIVE_EXAMPLE_INPUT
        },
        {
            "role": "assistant",
            "content": ONE_SHOT_DESCRIPTIVE_EXAMPLE_OUTPUT
        },
        # --- Actual task ---
        {
            "role": "user",
            "content": user_content
        }
    ]

def get_descriptive_summary_zero_shot_chain_of_thought_prompt(user_content):
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful data scientist for software engineering. Your job is to create a descriptive summary and a title explaining a software module's overall behaviour, architecture, and how the components interact within the cluster. "
                "When given a task, always reason through the problem step by step before producing your final answer. "
                "This ensures your summary accurately reflects the architecture and interactions rather than surface-level details."
            )
        },
        {
            "role": "user",
            "content": user_content + COT_DESCRIPTIVE
        }
    ]

def get_descriptive_summary_prompt(semantic_summaries, descriptive_summaries, prompt_technique):
    sections = []

    if semantic_summaries:
        semantic_content = "---------------\n".join(semantic_summaries)
        sections.append(f"<semantic_summaries>\n{semantic_content}\n</semantic_summaries>")

    if descriptive_summaries:
        descriptive_content = "---------------\n".join(descriptive_summaries)
        sections.append(f"<descriptive_summaries>\n{descriptive_content}\n</descriptive_summaries>")

    user_content = "Please create a high-level descriptive summary for the following:\n" + "\n".join(sections)

    match prompt_technique:
        case "zero-shot":
            return get_descriptive_summary_zero_shot_prompt(user_content)
        case "one-shot":
            return get_descriptive_summary_one_shot_prompt(user_content)
        case "chain-of-thought":
            return get_descriptive_summary_zero_shot_chain_of_thought_prompt(user_content)


def do_llm_call(prompt) -> str:

    # Convert prompt into tokens
    inputs = tokenizer.apply_chat_template(
        prompt,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
        truncation=True,
        max_length=7680
    ).to(model.device)

    # Generate response
    outputs = model.generate(
      **inputs,
      max_new_tokens=512, # These are the newly generated response tokens. This caps how long the response can be. 512 tokens is roughly 350-400 words. Without this cap the model could generate forever.
      temperature=0.5,
      top_p=0.8,
      do_sample=True,
      pad_token_id=tokenizer.eos_token_id
    )

    # Convert the output back from tokens into human-readable text and display it
    input_length = inputs['input_ids'].shape[1]
    response = tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)

    # Clean up after each call
    del inputs, outputs
    torch.cuda.empty_cache()
    gc.collect()

    return response

def get_semantic_summary(file_content: str, prompt_technique):
  return do_llm_call(get_semantic_summary_prompt(file_content, prompt_technique))

def get_descriptive_summary(semantic_summaries, descriptive_summaries, prompt_technique):
  return do_llm_call(get_descriptive_summary_prompt(semantic_summaries, descriptive_summaries, prompt_technique))

def remove_license_header(content: str) -> str:
    # Removes the first /* ... */ Comment at the beginning of a file
    return re.sub(r'^\s*/\*.*?\*/\s*', '', content, count=1, flags=re.DOTALL)

# returns descriptive summary
def process_directory(directory, cluster_file_names, prompt_technique):
    subdirs = [p for p in directory.iterdir() if p.is_dir()]
    files   = [p for p in directory.iterdir() if p.is_file()]
    descriptive_summaries = []
    semantic_summaries = []

    # Get descriptive summary for every subfolder in a recursiv way
    for subdir in subdirs:
        descriptive_summary = process_directory(subdir, cluster_file_names, prompt_technique)
        if descriptive_summary is not None:
          descriptive_summaries.append(descriptive_summary)

    # Get semantic summary for every file in current folder
    for file in files:
      if file.name in cluster_file_names:
        print('opened', file)
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            semantic_summary = get_semantic_summary(remove_license_header(content), prompt_technique)
            semantic_summaries.append(semantic_summary)

    if (len(semantic_summaries) == 0) and (len(descriptive_summaries) == 0):
      return None

    if (len(semantic_summaries) == 0) and (len(descriptive_summaries) == 1):
      return descriptive_summaries[0]

    print('return descriptive summary for', directory)
    return get_descriptive_summary(semantic_summaries, descriptive_summaries, prompt_technique)

def get_clusters(rsf_file_path):
    clusters = defaultdict(list)
    with open(rsf_file_path, "r") as infile:
        for line in infile:
            parts = line.strip().split()
            if len(parts) != 3 or parts[0] != "contain":
                continue
            cluster_name, entity = parts[1], parts[2]

            if cluster_name.endswith(".ss"):
                # this is the case for the acdc.rsf
                cluster_name = cluster_name[:-3]

            clusters[cluster_name].append(entity)

    return clusters

# ==========================================
# 6. True Start after model was loaded and function declared
# ==========================================


## filtered.rsf uses some files that are out of /lucene/lucene/codecs scope as the source or target location
## was within /lucene/lucene/codecs. All these files were found in this folder:
SECOND_SOURCE_CODE_DIR = Path("/scratch/hpc-prf-dssecs/group-9/lucene/lucene/core/src/java/org/apache/lucene/codecs")
SOURCE_CODE_DIR = Path("/scratch/hpc-prf-dssecs/group-9/lucene/lucene/codecs")
BASE_RSF_FILES = Path("/scratch/hpc-prf-dssecs/group-9/file-based-rsf")
BASE_OUTPUT_DIR = Path("/scratch/hpc-prf-dssecs/group-9/hierarchical_summarization")
VALID_RSF_FILE_NAME = {"arc", "wca_UEMNM", "wca_UEM", "limbo", "acdc"}
VALID_PROMPT_TECHNIQUES = {"zero-shot", "one-shot", "chain-of-thought"}

cluster_algo_name = sys.argv[1]
prompt_technique = sys.argv[2]

if cluster_algo_name not in VALID_RSF_FILE_NAME:
    print(f"unknown 1. argument: {cluster_algo_name}")
    sys.exit(1)

if prompt_technique not in VALID_PROMPT_TECHNIQUES:
    print(f"unknown 2. argument: {prompt_technique}")
    sys.exit(1)

path_to_clusters = BASE_RSF_FILES / f"{cluster_algo_name}.rsf"
clusters = get_clusters(path_to_clusters)

for cluster_name, entities in clusters.items():
    first_descriptive_summary = process_directory(SOURCE_CODE_DIR, entities, prompt_technique)
    second_descriptive_summary = process_directory(SECOND_SOURCE_CODE_DIR, entities, prompt_technique)

    if first_descriptive_summary and second_descriptive_summary:
        # combine summaries if cluster had files in in both directories
        final_descriptive_summary = get_descriptive_summary([], [first_descriptive_summary, second_descriptive_summary], prompt_technique)
    else:
        final_descriptive_summary = first_descriptive_summary or second_descriptive_summary

    output_path = BASE_OUTPUT_DIR / f"{cluster_algo_name}/{prompt_technique}/{cluster_name}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(final_descriptive_summary)
