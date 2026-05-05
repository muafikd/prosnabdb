<template>
  <div class="rich-text-editor">
    <div class="toolbar">
      <el-button size="small" :type="isActive('bold') ? 'primary' : 'default'" @mousedown.prevent="format('bold')" title="Жирный">
        <strong>Ж</strong>
      </el-button>
      <el-button size="small" :type="isActive('italic') ? 'primary' : 'default'" @mousedown.prevent="format('italic')" title="Курсив">
        <em>К</em>
      </el-button>
      <el-button size="small" :type="isActive('underline') ? 'primary' : 'default'" @mousedown.prevent="format('underline')" title="Подчеркнутый">
        <u>Ч</u>
      </el-button>
      <el-button size="small" @mousedown.prevent="format('removeFormat')" title="Удалить форматирование">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
    <div 
      ref="editor"
      class="editor-content"
      contenteditable="true"
      @input="handleInput"
      @keydown="handleKeydown"
      @keyup="updateActiveStates"
      @mouseup="updateActiveStates"
      @focus="updateActiveStates"
      @blur="handleBlur"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { Delete } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string;
  placeholder?: string;
}>()

const emit = defineEmits(['update:modelValue', 'blur'])

const editor = ref<HTMLElement | null>(null)
const activeFormats = ref<Record<string, boolean>>({
  bold: false,
  italic: false,
  underline: false
})

// Keep track of cursor position when formatting is applied
const format = (command: string) => {
  document.execCommand(command, false, '')
  updateActiveStates()
  editor.value?.focus()
  handleInput() // Force update model after format
}

const isActive = (command: string) => {
  return activeFormats.value[command]
}

const updateActiveStates = () => {
  activeFormats.value.bold = document.queryCommandState('bold')
  activeFormats.value.italic = document.queryCommandState('italic')
  activeFormats.value.underline = document.queryCommandState('underline')
}

const handleInput = () => {
  if (editor.value) {
    let content = editor.value.innerHTML
    // Basic cleanup of empty paragraphs if needed
    if (content === '<br>') content = ''
    emit('update:modelValue', content)
  }
}

const handleBlur = (e: FocusEvent) => {
  emit('blur', e)
}

// Handle Enter to create <br> or <div> instead of weird paragraph nesting depending on browser
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    // Let contenteditable handle it naturally for now, 
    // modern browsers create <div> or <p> which we will parse in the backend.
  }
}

// Watch for external changes (like initial load)
watch(() => props.modelValue, (newVal) => {
  if (editor.value && editor.value.innerHTML !== newVal) {
    // Only update if it's different to prevent cursor jumping
    editor.value.innerHTML = newVal || ''
  }
})

onMounted(() => {
  if (editor.value) {
    editor.value.innerHTML = props.modelValue || ''
  }
})
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  background-color: #fff;
}

.toolbar {
  padding: 8px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  gap: 4px;
}

.editor-content {
  min-height: 100px;
  padding: 12px;
  outline: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
}

.editor-content:focus {
  background-color: #fafbfc;
}

/* Make block elements behave nicely */
.editor-content :deep(p), 
.editor-content :deep(div) {
  margin: 0 0 0.5em 0;
}
.editor-content :deep(p:last-child), 
.editor-content :deep(div:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(b),
.editor-content :deep(strong) {
  font-weight: bold;
}
.editor-content :deep(i),
.editor-content :deep(em) {
  font-style: italic;
}
.editor-content :deep(u) {
  text-decoration: underline;
}
</style>
