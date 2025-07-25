// EngineQ: An AI-enabled music management system.
// Copyright (C) 2025  Mikayel Grigoryan
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// 
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// 
// For inquiries, contact: michael.grigoryan25@gmail.com
import postgres from "postgres";

let __sql: postgres.Sql<{}>;

if (process.env.NODE_ENV === "production") {
  __sql = postgres(process.env!.POSTGRES_URL!);
} else {
  if (!(global as any).__sql) {
    (global as any).__sql = postgres(process.env!.POSTGRES_URL!);
  }

  __sql = (global as any).__sql;
}

export { __sql as sql };
