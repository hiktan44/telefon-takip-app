-- Telefonlar tablosu
create table phones (
  id bigint generated by default as identity primary key,
  model text not null,
  brand text,
  price decimal,
  specs jsonb,
  source text,
  date_added timestamp with time zone default timezone('utc'::text, now())
);

-- Referans telefonlar tablosu
create table reference_phones (
  id bigint generated by default as identity primary key,
  model text not null,
  brand text,
  release_date date,
  base_price decimal,
  specs jsonb,
  date_added timestamp with time zone default timezone('utc'::text, now())
);

-- Fiyat geçmişi tablosu
create table price_history (
  id bigint generated by default as identity primary key,
  phone_id bigint references phones(id),
  price decimal,
  date date,
  source text,
  created_at timestamp with time zone default timezone('utc'::text, now())
);

-- İndeksler
create index idx_phones_model on phones(model);
create index idx_phones_brand on phones(brand);
create index idx_reference_phones_model on reference_phones(model);
create index idx_reference_phones_brand on reference_phones(brand);
create index idx_price_history_phone_id on price_history(phone_id);
create index idx_price_history_date on price_history(date);

-- Row Level Security (RLS) politikaları
alter table phones enable row level security;
alter table reference_phones enable row level security;
alter table price_history enable row level security;

-- Herkes okuyabilir
create policy "Herkes telefonları görebilir"
  on phones for select
  using (true);

create policy "Herkes referans telefonları görebilir"
  on reference_phones for select
  using (true);

create policy "Herkes fiyat geçmişini görebilir"
  on price_history for select
  using (true);

-- Sadece kimlik doğrulaması yapılmış kullanıcılar ekleyebilir/düzenleyebilir
create policy "Kimlik doğrulamalı kullanıcılar telefon ekleyebilir"
  on phones for insert
  with check (auth.role() = 'authenticated');

create policy "Kimlik doğrulamalı kullanıcılar referans telefon ekleyebilir"
  on reference_phones for insert
  with check (auth.role() = 'authenticated');

create policy "Kimlik doğrulamalı kullanıcılar fiyat geçmişi ekleyebilir"
  on price_history for insert
  with check (auth.role() = 'authenticated'); 