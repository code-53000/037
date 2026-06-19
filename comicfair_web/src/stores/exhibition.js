import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getActiveExhibitions } from '@/api/exhibitions'

export const useExhibitionStore = defineStore('exhibition', () => {
  const currentId = ref(parseInt(localStorage.getItem('cf_exhibition_id') || '1'))
  const current = ref(null)
  const list = ref([])

  async function loadList() {
    const data = await getActiveExhibitions()
    list.value = data
    if (!current.value && data.length > 0) {
      setCurrent(data[0])
    }
    return data
  }

  function setCurrent(exhibition) {
    current.value = exhibition
    currentId.value = exhibition.id
    localStorage.setItem('cf_exhibition_id', String(exhibition.id))
  }

  function getCurrent() {
    if (!current.value && list.value.length > 0) {
      const found = list.value.find((e) => e.id === currentId.value)
      if (found) {
        current.value = found
      }
    }
    return current.value
  }

  return {
    currentId,
    current,
    list,
    loadList,
    setCurrent,
    getCurrent,
  }
})
