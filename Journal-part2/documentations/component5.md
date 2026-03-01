# Component 5: LSTM-Inspired Memory Gates + RL Training

## Purpose
Intelligent memory management system using LSTM-inspired gates with reinforcement learning to decide what memories to keep, fade, or surface for conversations.

## Core Functions
- **Memory Gate Operations**: Three neural networks (Forget, Input, Output) for memory decisions
- **Memory State Management**: Track importance, access patterns, and decay over time
- **Context Assembly**: Select optimal memories for Gemini conversations within token budget
- **Reinforcement Learning**: Optimize gate parameters based on user engagement and satisfaction
- **Personal Adaptation**: Learn individual memory preferences and patterns

## Architecture Components

### Three Gate Networks
- **Forget Gate**: DistilBERT fine-tuned to predict memory fade probability (0-1 score)
  - Considers: time since creation, resolution status, access frequency, emotional intensity
  - Output: Should this memory be forgotten or preserved?

- **Input Gate**: RoBERTa fine-tuned to score new memory importance (0-1 score)  
  - Considers: emotional significance, novelty, future events, relationships mentioned
  - Output: How important is this new memory for long-term storage?

- **Output Gate**: BERT fine-tuned to rank memory relevance for current context (0-1 score)
  - Considers: semantic similarity, temporal relevance, emotional match, user engagement
  - Output: How relevant is this memory for the current conversation?

### Memory State Manager
- **Memory Vectors**: 768-dim embeddings + temporal/emotional/engagement metadata
- **Decay Tracking**: Automatic importance reduction over time with user-specific rates
- **Access Patterns**: Track how often memories are referenced in conversations
- **Relationship Mapping**: Connect related memories for context clustering

### RL Optimization System
- **State Representation**: Current conversation context, user emotional state, available memories
- **Action Space**: Adjust gate thresholds, promote/demote memories, change context window size
- **Reward Function**: User engagement (40%) + conversation quality (30%) + memory relevance (30%)
- **Policy Network**: PPO-based optimization of gate parameters for individual users

## Processing Pipeline

### Memory Creation
1. **New Entry Processing**: Receive EngineeredFeatures from Component 4
2. **Input Gate Scoring**: Evaluate importance for long-term storage
3. **Memory Vector Creation**: Generate embedding + metadata storage
4. **Initial Classification**: Assign memory type and importance tier

### Memory Updates
1. **Periodic Rescoring**: Recalculate all gate scores based on recent activity
2. **Decay Application**: Apply time-based and disuse-based decay functions
3. **Access Tracking**: Update engagement metrics when memories are referenced
4. **Relationship Updates**: Maintain connections between related memories

### Context Assembly
1. **Output Gate Filtering**: Score all memories for current conversation relevance
2. **Semantic Ranking**: Use embedding similarity for topic relevance
3. **Diversity Selection**: Ensure varied memory types (emotional, factual, relational)
4. **Token Optimization**: Fit maximum relevant context within 2000 token budget

### RL Training Loop
1. **Experience Collection**: Track user interactions with AI responses
2. **Reward Calculation**: Score based on engagement, satisfaction, conversation quality
3. **Policy Update**: Adjust gate parameters using PPO optimization
4. **Performance Validation**: A/B test new parameters against baseline

## Technical Implementation

### Gate Network Architecture
- **Model Base**: Pre-trained transformers fine-tuned on memory tasks
- **Input Features**: 90-dim engineered features + 768-dim text embeddings
- **Architecture**: 3-layer networks (128→64→32→1) with sigmoid outputs
- **Training**: Supervised learning on user feedback + RL optimization

### Memory Storage
- **Vector Database**: Pinecone for efficient similarity search and retrieval
- **Metadata Store**: PostgreSQL for structured memory information
- **Cache Layer**: Redis for frequently accessed memory contexts
- **Compression**: Efficient storage of embeddings and feature vectors

### RL Configuration
- **Algorithm**: Proximal Policy Optimization (PPO) for stable learning
- **Exploration**: ε-greedy with decaying exploration rate
- **Update Frequency**: Weekly parameter updates based on accumulated experience
- **Validation**: Hold-out test set for preventing overfitting

## Performance Requirements
- **Gate Inference**: <100ms for single memory scoring
- **Context Assembly**: <500ms for optimal context selection from 1000+ memories
- **Memory Creation**: <200ms for new memory processing and storage
- **RL Training**: <30min for weekly parameter optimization

## Quality Metrics
- **Memory Relevance**: 90%+ user validation of surfaced memories as relevant
- **Context Quality**: 85%+ user satisfaction with conversation context
- **Retention Accuracy**: 95% agreement with user preferences on memory importance
- **Engagement Improvement**: 15%+ increase in conversation engagement with RL optimization

## Data Models
- **MemoryItem**: content_summary, embeddings, gate_scores, access_metadata, relationships
- **GateScores**: forget_score, input_score, output_score, confidence, timestamp
- **MemoryContext**: selected_memories, relevance_scores, token_usage, assembly_metadata
- **RLExperience**: state, action, reward, next_state for policy learning

## Integration Points
- **Input**: Receives EngineeredFeatures from Component 4
- **Output**: Provides assembled context to Component 6 (Gemini Integration)
- **Feedback**: Learns from user engagement signals and conversation quality
- **Storage**: Interfaces with vector database and structured storage systems