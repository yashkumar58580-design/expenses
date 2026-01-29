import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'TERA_SUPABASE_URL'
const supabaseKey = 'TERA_SUPABASE_ANON_KEY'

export const supabase = createClient(supabaseUrl, supabaseKey)
