---
name: travel-local-search
description: >
  Find current real-world places and travel options around a specified location: pharmacies,
  restaurants, shops, exchange offices, hotels, attractions, routes, local transport and flights.
  Use for near-me/local searches, route planning, opening hours, official sites, booking/ordering,
  or options along a stated walking direction.
metadata:
  version: "1.0"
  capabilities:
    - local-search
    - pharmacy-search
    - restaurant-search
    - shop-search
    - hotel-search
    - route-planning
    - transport-search
    - opening-hours
  triggers:
    - рядом
    - поблизости
    - найди
    - аптека рядом
    - ресторан
    - магазин
    - отель
    - маршрут
    - транспорт
    - Стамбул
---

# Travel and Local Search

## Workflow

1. Establish the geographic anchor and, if relevant, direction of travel.
2. Use current sources for businesses, hours, transport, prices, routes and availability.
3. Prefer options that genuinely fit the user's route and constraints.
4. For each recommended place include useful available details such as:
   - name;
   - why it fits;
   - address;
   - distance/walking time when known;
   - hours;
   - official site or booking/order path;
   - important practical notes.
5. Use maps/local business tools when they improve the answer.

Do not recommend places in the opposite direction merely because they rank highly unless there is a
clear reason and it is stated.
