import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

function createShim() {
  const error = new Error('Supabase ni konfiguriran: dodaj VITE_SUPABASE_URL in VITE_SUPABASE_ANON_KEY')
  const builder = {
    async select() { return { data: null, error } },
    async insert() { return { data: null, error } },
    order() { return builder }
  }
  return {
    from() { return builder }
  } as any
}

export const supabase = (url && anonKey)
  ? createClient(String(url), String(anonKey))
  : createShim()